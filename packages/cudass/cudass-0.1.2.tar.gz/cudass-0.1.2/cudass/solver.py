"""Main solver interface for the CUDA sparse linear solver."""

from typing import Optional, Tuple

import torch

from cudass.backends.factory import create_backend
from cudass.factorization.cache import FactorizationCache
from cudass.factorization.refactorization import RefactorizationManager
from cudass.types import MatrixType, validate_matrix_type_shape


class _StubBackend:
    """Stub backend; replaced by factory at first update_matrix/solve."""

    @property
    def backend_name(self) -> str:
        return "stub"

    def update_matrix(
        self,
        A_sparse: Tuple[torch.Tensor, torch.Tensor, int, int],
        structure_changed: bool = False,
    ) -> None:
        raise NotImplementedError("_backend not wired; set by factory at first use")

    def solve(self, b: torch.Tensor) -> torch.Tensor:
        raise NotImplementedError("_backend not wired; set by factory at first use")


class CUDASparseSolver:
    """High-performance CUDA sparse linear solver.

    Supports multiple matrix types with cuDSS (primary), cuSOLVER Dense
    (fallback for singular/rectangular), and cuSolverSp (OOM fallback).

    Args:
        matrix_type: Matrix type (must be specified explicitly).
        use_cache: Whether to cache factorizations.
        dtype: Floating point precision (torch.float32 or torch.float64).
        device: CUDA device (auto-detected from inputs if None).
        prefer_dense: If True, prefer cusolver_dn over cudss when applicable.
        force_backend: If set to 'cudss', 'cusolver_dn', or 'cusolver_sp', use that
            backend and do not fallback.

    Raises:
        RuntimeError: If CUDA is not available.
    """

    def __init__(
        self,
        matrix_type: MatrixType,
        use_cache: bool = True,
        dtype: torch.dtype = torch.float64,
        device: Optional[torch.device] = None,
        prefer_dense: bool = False,
        force_backend: Optional[str] = None,
    ):
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA is not available")
        self._matrix_type = matrix_type
        self._use_cache = use_cache
        self._dtype = dtype
        self._device = device
        self._prefer_dense = prefer_dense
        self._force_backend = force_backend
        self._A_sparse: Optional[Tuple[torch.Tensor, torch.Tensor, int, int]] = None
        self._matrix_set = False
        self._backend: object = _StubBackend()
        self._cache = FactorizationCache(max_size=100) if use_cache else None
        self._last_shape: Optional[Tuple[int, int]] = None
        self._refactor = RefactorizationManager()
        self._prev_A_sparse: Optional[Tuple[torch.Tensor, torch.Tensor, int, int]] = None

    @property
    def backend_name(self) -> str:
        """Backend in use: 'cudss', 'cusolver_dn', 'cusolver_sp', or 'stub' before first solve.

        Returns:
            str: Backend name.
        """
        return getattr(self._backend, "backend_name", "stub")

    def update_matrix(
        self,
        A_sparse: Tuple[torch.Tensor, torch.Tensor, int, int],
        structure_changed: Optional[bool] = None,
    ) -> None:
        """Set or update the matrix A: factorize and cache.

        Call before the first solve; call again whenever A changes.

        Args:
            A_sparse: Sparse matrix tuple (index, value, m, n).
            structure_changed: If True, sparsity pattern changed (full refactorization);
                if False, only values changed (fast update). If None, auto-detect from
                previous A.

        Raises:
            ValueError: If matrix shape/type incompatible with solver, or invalid dtypes/devices.
        """
        index, value, m, n = A_sparse
        if index.dim() != 2 or index.shape[0] != 2:
            raise ValueError("index must be [2, nnz]")
        if value.dim() != 1 or value.shape[0] != index.shape[1]:
            raise ValueError("value must be [nnz] and match index.shape[1]")
        if index.dtype != torch.int64:
            raise ValueError("index must be torch.int64")
        if value.dtype not in (torch.float32, torch.float64):
            raise ValueError("value must be torch.float32 or torch.float64")
        if not index.is_cuda or not value.is_cuda:
            raise ValueError("index and value must be on CUDA")
        if m <= 0 or n <= 0:
            raise ValueError("m and n must be positive")
        validate_matrix_type_shape(self._matrix_type, m, n)

        if self._device is None:
            self._device = index.device
        if index.device != self._device or value.device != self._device:
            raise ValueError("A_sparse must be on the same device as the solver")

        if structure_changed is None:
            needs, structure_changed = self._refactor.should_refactorize(
                self._prev_A_sparse, A_sparse
            )
            if not needs:
                self._A_sparse = A_sparse
                self._matrix_set = True
                self._prev_A_sparse = A_sparse
                return

        shape = (m, n)
        if isinstance(self._backend, _StubBackend) or self._last_shape != shape:
            self._backend = create_backend(
                self._matrix_type,
                shape,
                self._device,
                value.dtype,
                use_cache=self._use_cache,
                cache=self._cache,
                prefer_dense=self._prefer_dense,
                force_backend=self._force_backend,
            )
            self._last_shape = shape

        self._A_sparse = A_sparse
        self._matrix_set = True
        self._prev_A_sparse = A_sparse
        self._backend.update_matrix(A_sparse, structure_changed or False)

    def solve(self, b: torch.Tensor) -> torch.Tensor:
        """Solve Ax = b using the current A from the last update_matrix.

        Args:
            b: RHS vector/matrix, shape [m] or [m, k], same dtype as A, on CUDA.

        Returns:
            Solution x, shape [n] or [n, k], same dtype and device as b.

        Raises:
            RuntimeError: If the backend solver fails or a CUDA error occurs.
            ValueError: If no matrix set (update_matrix first) or shapes/dtypes/devices invalid.
        """
        if not self._matrix_set:
            raise ValueError("update_matrix must be called before solve")
        _, _, m, n = self._A_sparse
        # For Ax=b with A (m,n): b is (m,) or (m,k), x is (n,) or (n,k)
        if b.dim() == 1:
            if b.shape[0] != m:
                raise ValueError(f"b must have shape [m] with m={m}; got {b.shape[0]}")
        elif b.dim() == 2:
            if b.shape[0] != m:
                raise ValueError(f"b must have shape [m,k] with m={m}; got {b.shape}")
        else:
            raise ValueError("b must be 1D [m] or 2D [m, k]")
        if b.dtype not in (torch.float32, torch.float64):
            raise ValueError("b must be torch.float32 or torch.float64")
        if not b.is_cuda:
            raise ValueError("b must be on CUDA")
        if self._device is not None and b.device != self._device:
            raise ValueError("b must be on the same device as the solver")

        try:
            return self._backend.solve(b)
        except RuntimeError:
            raise
