"""cuDSS backend: COO->CSR, ANALYSIS/FACTORIZATION/SOLVE, multiple RHS.

Prefers our cudss_bindings; falls back to nvmath's cudss only if our bindings
are not built/importable.
"""

from typing import Any, Optional, Tuple

import torch

from cudass.backends.base import BackendBase
from cudass.cuda.cuda_types import CUDA_R_32F, CUDA_R_32I, CUDA_R_64F
from cudass.types import MatrixType

# Prefer our own cudss_bindings; fall back to nvmath only if ours are not available
_cudss = None
_cudss_import_error = None

try:
    import cudass.cuda.bindings.cudss_bindings as _cudss
except ImportError as e:
    _cudss_import_error = str(e)
    _nvmath_cudss = None
    try:
        from nvmath import cudss as _nvmath_cudss
    except ImportError:
        try:
            from nvmath.bindings import cudss as _nvmath_cudss
        except ImportError:
            pass

    if _nvmath_cudss is not None:
        # Adapter: nvmath -> our bindings API (create_handle, matrix_create_csr row_end_ptr=, etc.)
        class _CudssApi:
            pass

        _api = _CudssApi()
        _api.create_handle = _nvmath_cudss.create
        _api.destroy_handle = _nvmath_cudss.destroy
        _api.config_create = _nvmath_cudss.config_create
        _api.config_destroy = _nvmath_cudss.config_destroy
        _api.data_create = _nvmath_cudss.data_create
        _api.data_destroy = _nvmath_cudss.data_destroy
        _api.set_stream = _nvmath_cudss.set_stream
        _api.matrix_destroy = _nvmath_cudss.matrix_destroy
        _api.matrix_set_values = _nvmath_cudss.matrix_set_values
        _api.execute = _nvmath_cudss.execute
        _api.CUDA_R_32F = CUDA_R_32F
        _api.CUDA_R_64F = CUDA_R_64F
        _api.CUDA_R_32I = CUDA_R_32I
        _api.CUDSS_MTYPE_GENERAL = int(_nvmath_cudss.MatrixType.GENERAL)
        _api.CUDSS_MTYPE_SYMMETRIC = int(_nvmath_cudss.MatrixType.SYMMETRIC)
        _api.CUDSS_MTYPE_SPD = int(_nvmath_cudss.MatrixType.SPD)
        _api.CUDSS_MVIEW_FULL = int(_nvmath_cudss.MatrixViewType.FULL)
        _api.CUDSS_BASE_ZERO = int(_nvmath_cudss.IndexBase.ZERO)
        _api.CUDSS_LAYOUT_COL_MAJOR = int(_nvmath_cudss.Layout.COL_MAJOR)
        _api.CUDSS_PHASE_ANALYSIS = int(_nvmath_cudss.Phase.ANALYSIS)
        _api.CUDSS_PHASE_FACTORIZATION = int(_nvmath_cudss.Phase.FACTORIZATION)
        _api.CUDSS_PHASE_SOLVE = int(_nvmath_cudss.Phase.SOLVE)

        def _nvmath_matrix_create_csr(
            m, n, nnz, row_start_ptr, col_indices_ptr, values_ptr,
            index_type, value_type, mtype, mview, index_base, row_end_ptr=0,
        ):
            return _nvmath_cudss.matrix_create_csr(
                m, n, nnz, row_start_ptr, 0, col_indices_ptr, values_ptr,
                index_type, value_type, mtype, mview, index_base,
            )

        _api.matrix_create_csr = _nvmath_matrix_create_csr

        def _nvmath_matrix_create_dn(nrows, ncols, ld, values_ptr, vt, layout):
            return _nvmath_cudss.matrix_create_dn(nrows, ncols, ld, values_ptr, vt, layout)

        _api.matrix_create_dn = _nvmath_matrix_create_dn
        _cudss = _api
        _cudss_import_error = None


def _coo_to_csr(
    index: torch.Tensor, value: torch.Tensor, m: int, n: int
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor]:
    """COO (index [2,nnz], value [nnz]) -> CSR rowStart (m+1), colIndices (nnz), values (nnz).

    Merges duplicate (i,j) by summing. cuDSS requires no duplicate column indices in a row.

    Args:
        index: COO indices [2, nnz].
        value: COO values [nnz].
        m: Number of rows.
        n: Number of columns.

    Returns:
        Tuple of (row_start [m+1], col_indices [nnz], values [nnz]).
    """
    nnz = index.shape[1]
    if nnz == 0:
        row_start = torch.zeros(m + 1, dtype=torch.int32, device=index.device)
        col_indices = torch.empty(0, dtype=torch.int32, device=index.device)
        values = torch.empty(0, dtype=value.dtype, device=value.device)
        return row_start, col_indices, values
    perm = torch.argsort(index[0] * (max(n, m) + 1) + index[1])
    idx_sorted = index[:, perm]
    val_sorted = value[perm].contiguous()
    rows, cols = idx_sorted[0], idx_sorted[1]
    # Coalesce duplicate (row,col): sum values. cuDSS forbids duplicates in a row.
    keys = rows * (max(n, m) + 1) + cols
    if keys.numel() > 1:
        run_end = (keys[1:] != keys[:-1]).nonzero(as_tuple=True)[0] + 1
        run_start = torch.cat([torch.tensor([0], device=keys.device, dtype=run_end.dtype), run_end])
        tail = torch.tensor([keys.numel()], device=keys.device, dtype=run_end.dtype)
        run_end = torch.cat([run_end, tail])
        rows = rows[run_start]
        cols = cols[run_start]
        pairs = zip(run_start.tolist(), run_end.tolist())
        values = torch.stack([val_sorted[s:e].sum() for s, e in pairs])
    else:
        values = val_sorted
    counts = torch.bincount(rows, minlength=m).to(torch.int32)
    z = torch.zeros(1, dtype=torch.int32, device=index.device)
    # cumsum of int32 promotes to int64; cuDSS with CUDA_R_32I expects int32
    row_start = torch.cat([z, torch.cumsum(counts, 0)], dim=0).to(torch.int32)
    col_indices = cols.to(torch.int32).contiguous()
    return row_start, col_indices, values


def _matrix_type_to_cudss_mtype(matrix_type: MatrixType) -> int:
    if matrix_type == MatrixType.GENERAL or matrix_type == MatrixType.GENERAL_RECTANGULAR:
        return _cudss.CUDSS_MTYPE_GENERAL
    if matrix_type == MatrixType.SYMMETRIC:
        return _cudss.CUDSS_MTYPE_SYMMETRIC
    if matrix_type == MatrixType.SPD:
        return _cudss.CUDSS_MTYPE_SPD
    raise ValueError(f"cuDSS does not support {matrix_type}")


def _dtype_to_value_type(dtype: torch.dtype) -> int:
    if dtype == torch.float32:
        return _cudss.CUDA_R_32F
    if dtype == torch.float64:
        return _cudss.CUDA_R_64F
    raise ValueError(f"dtype must be float32 or float64, got {dtype}")


class CUDSSBackend(BackendBase):
    """cuDSS backend for GENERAL, SYMMETRIC, SPD, and tentative GENERAL_RECTANGULAR."""

    @property
    def backend_name(self) -> str:
        return "cudss"

    def __init__(
        self,
        matrix_type: MatrixType,
        device: torch.device,
        dtype: torch.dtype,
        use_cache: bool = True,
        cache: Optional[Any] = None,
    ):
        if _cudss is None:
            raise RuntimeError(f"cudss_bindings not available: {_cudss_import_error}")
        self._matrix_type = matrix_type
        self._device = device
        self._dtype = dtype
        self._use_cache = use_cache
        self._cache = cache
        self._handle: Optional[int] = None
        self._config: Optional[int] = None
        self._data: Optional[int] = None
        self._mat_a: Optional[int] = None
        self._row_start: Optional[torch.Tensor] = None
        self._col_indices: Optional[torch.Tensor] = None
        self._values: Optional[torch.Tensor] = None  # keep CSR values alive; cuDSS does not copy
        self._m = 0
        self._n = 0
        self._nnz = 0

    @property
    def device(self) -> torch.device:
        return self._device

    @property
    def dtype(self) -> torch.dtype:
        return self._dtype

    def _ensure_handle_config_data(self) -> None:
        if self._handle is not None:
            return
        self._handle = _cudss.create_handle()
        self._config = _cudss.config_create()
        self._data = _cudss.data_create(self._handle)
        stream = torch.cuda.current_stream(self._device).cuda_stream
        _cudss.set_stream(self._handle, stream)

    def _destroy_mat_a(self) -> None:
        if self._mat_a is not None:
            _cudss.matrix_destroy(self._mat_a)
            self._mat_a = None
        self._row_start = None
        self._col_indices = None
        self._values = None

    def _cache_key(self, index: torch.Tensor, m: int, n: int) -> str:
        h = hash((m, n, index.shape[1], index.data_ptr()))
        return f"cudss_{m}_{n}_{h}"

    def update_matrix(
        self,
        A_sparse: Tuple[torch.Tensor, torch.Tensor, int, int],
        structure_changed: bool = False,
    ) -> None:
        index, value, m, n = A_sparse
        vt = _dtype_to_value_type(value.dtype)
        mtype = _matrix_type_to_cudss_mtype(self._matrix_type)
        row_start, col_indices, values = _coo_to_csr(index, value, m, n)
        nnz = values.shape[0]  # after coalesce, may differ from index.shape[1]

        def _run_phase(phase: int) -> None:
            buf_b = torch.zeros(n, 1, dtype=values.dtype, device=self._device)
            buf_x = torch.zeros(n, 1, dtype=values.dtype, device=self._device)
            layout = _cudss.CUDSS_LAYOUT_COL_MAJOR
            mb = _cudss.matrix_create_dn(n, 1, n, buf_b.data_ptr(), vt, layout)
            mx = _cudss.matrix_create_dn(n, 1, n, buf_x.data_ptr(), vt, layout)
            try:
                _cudss.execute(
                    self._handle, phase, self._config, self._data,
                    self._mat_a, mx, mb,
                )
            finally:
                _cudss.matrix_destroy(mb)
                _cudss.matrix_destroy(mx)

        cache = self._cache
        ck = self._cache_key(index, m, n) if cache else None
        if self._use_cache and cache and ck:
            cached = cache.get(ck, self._device)
            if cached is not None and not structure_changed:
                (h, cfg, d, ma, rs, ci) = cached
                self._handle, self._config, self._data = h, cfg, d
                self._mat_a = ma
                self._row_start, self._col_indices = rs, ci
                self._values = values
                _cudss.matrix_set_values(self._mat_a, values.data_ptr())
                _run_phase(_cudss.CUDSS_PHASE_FACTORIZATION)
                self._m, self._n, self._nnz = m, n, nnz
                return

        self._ensure_handle_config_data()
        struct_or_size = (
            structure_changed or self._mat_a is None
            or self._m != m or self._n != n or self._nnz != nnz
        )
        if struct_or_size:
            self._destroy_mat_a()
            if self._data is not None:
                _cudss.data_destroy(self._handle, self._data)
            self._data = _cudss.data_create(self._handle)
            # cuDSS CSR: rowStart (m+1). rowEnd: pass 0 (NULL); cuDSS uses rowStart[i+1] as end.
            self._mat_a = _cudss.matrix_create_csr(
                m, n, nnz,
                row_start.data_ptr(), col_indices.data_ptr(), values.data_ptr(),
                _cudss.CUDA_R_32I, vt, mtype, _cudss.CUDSS_MVIEW_FULL, _cudss.CUDSS_BASE_ZERO,
                row_end_ptr=0,
            )
            self._row_start = row_start
            self._col_indices = col_indices
            self._values = values
            _run_phase(_cudss.CUDSS_PHASE_ANALYSIS)
            _run_phase(_cudss.CUDSS_PHASE_FACTORIZATION)
        else:
            self._values = values
            _cudss.matrix_set_values(self._mat_a, values.data_ptr())
            _run_phase(_cudss.CUDSS_PHASE_FACTORIZATION)
        self._m, self._n, self._nnz = m, n, nnz
        if self._use_cache and cache and ck:
            ent = (
                self._handle, self._config, self._data,
                self._mat_a, self._row_start, self._col_indices,
            )
            cache.put(ck, ent, self._device)

    def solve(self, b: torch.Tensor) -> torch.Tensor:
        n = self._n
        if b.dim() == 1:
            nrhs = 1
            b_ = b.unsqueeze(1).contiguous()
        else:
            nrhs = b.shape[1]
            b_ = b.contiguous()
        # cuDSS expects column-major: column j stored at [j*n : (j+1)*n].
        # b_ is [n, nrhs] row-major; b_.T.contiguous() gives [nrhs, n] whose first n
        # elements are b_[:,0], i.e. column-major layout for n x nrhs.
        b_t = b_.T.contiguous()
        x_buf = torch.empty(nrhs, n, device=b.device, dtype=b.dtype)
        vt = _dtype_to_value_type(b.dtype)
        _cudss.set_stream(
            self._handle,
            int(torch.cuda.current_stream(self._device).cuda_stream),
        )
        mat_b = _cudss.matrix_create_dn(
            n, nrhs, n, b_t.data_ptr(), vt, _cudss.CUDSS_LAYOUT_COL_MAJOR
        )
        mat_x = _cudss.matrix_create_dn(
            n, nrhs, n, x_buf.data_ptr(), vt, _cudss.CUDSS_LAYOUT_COL_MAJOR
        )
        try:
            _cudss.execute(
                self._handle,
                _cudss.CUDSS_PHASE_SOLVE,
                self._config,
                self._data,
                self._mat_a,
                mat_x,
                mat_b,
            )
        finally:
            _cudss.matrix_destroy(mat_b)
            _cudss.matrix_destroy(mat_x)
        torch.cuda.current_stream(self._device).synchronize()
        x = x_buf.T
        return x.squeeze(1) if nrhs == 1 else x
