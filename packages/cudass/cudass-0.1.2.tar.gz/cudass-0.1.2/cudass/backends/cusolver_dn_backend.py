"""cuSOLVER Dense backend: densify, potrs/sytrs/getrs/gels/gesvd/syevd."""

from typing import Any, Optional, Tuple

import torch

from cudass.backends.base import BackendBase
from cudass.types import MatrixType


def select_cusolver_routine(matrix_type: MatrixType, shape: Tuple[int, int]) -> str:
    """Select routine: potrs, sytrs, syevd, getrs, gels, gesvd.

    Args:
        matrix_type: MatrixType (SPD, SYMMETRIC, GENERAL, etc.).
        shape: (m, n) matrix dimensions.

    Returns:
        str: One of 'potrs', 'sytrs', 'syevd', 'getrs', 'gels', 'gesvd'.
    """
    m, n = shape
    if matrix_type == MatrixType.SPD:
        return "potrs"
    if matrix_type == MatrixType.SYMMETRIC:
        return "sytrs"
    if matrix_type == MatrixType.SYMMETRIC_SINGULAR:
        return "syevd"
    if matrix_type == MatrixType.GENERAL_SINGULAR:
        return "gesvd"
    if matrix_type == MatrixType.GENERAL_RECTANGULAR_SINGULAR:
        return "gesvd"
    if matrix_type == MatrixType.GENERAL_RECTANGULAR or m != n:
        return "gels" if m > n else "gesvd"
    return "getrs"


def _sparse_to_dense(index: torch.Tensor, value: torch.Tensor, m: int, n: int) -> torch.Tensor:
    try:
        from cudass.cuda.kernels import sparse_to_dense as _s2d
        return _s2d(index, value, m, n)
    except RuntimeError:
        # Fallback when kernel not built: torch sparse to_dense on GPU
        s = torch.sparse_coo_tensor(index, value, (m, n), device=index.device, dtype=value.dtype)
        return s.to_dense()


class CusolverDnBackend(BackendBase):
    """Dense backend using torch.linalg (cuSOLVER/cuBLAS on CUDA)."""

    @property
    def backend_name(self) -> str:
        return "cusolver_dn"

    def __init__(
        self,
        matrix_type: MatrixType,
        device: torch.device,
        dtype: torch.dtype,
        use_cache: bool = True,
        cache: Optional[Any] = None,
    ):
        self._matrix_type = matrix_type
        self._device = device
        self._dtype = dtype
        self._routine: Optional[str] = None
        self._A_dense: Optional[torch.Tensor] = None
        self._m = 0
        self._n = 0
        self._L: Optional[torch.Tensor] = None
        self._LU: Optional[torch.Tensor] = None
        self._piv: Optional[torch.Tensor] = None

    @property
    def device(self) -> torch.device:
        return self._device

    @property
    def dtype(self) -> torch.dtype:
        return self._dtype

    def update_matrix(
        self,
        A_sparse: Tuple[torch.Tensor, torch.Tensor, int, int],
        structure_changed: bool = False,
    ) -> None:
        index, value, m, n = A_sparse
        self._A_dense = _sparse_to_dense(index, value, m, n)
        self._m, self._n = m, n
        self._routine = select_cusolver_routine(self._matrix_type, (m, n))
        self._L = None
        self._LU = None
        self._piv = None
        if self._routine == "potrs":
            self._L = torch.linalg.cholesky(self._A_dense)
        elif self._routine == "getrs":
            lu_res = torch.linalg.lu_factor_ex(self._A_dense, check_errors=False)
            self._LU, self._piv = lu_res[0], lu_res[1]

    def solve(self, b: torch.Tensor) -> torch.Tensor:
        b_was_1d = b.dim() == 1
        if b_was_1d:
            b = b.unsqueeze(1)
        A, r = self._A_dense, self._routine
        if r == "potrs":
            x = torch.cholesky_solve(b, self._L)
        elif r == "sytrs":
            x = torch.linalg.solve(A, b)
        elif r == "getrs":
            x = torch.linalg.lu_solve(self._LU, self._piv, b)
        elif r == "gels":
            res = torch.linalg.lstsq(A, b, rcond=None)
            x = res.solution if hasattr(res, "solution") else res[0]
        elif r == "gesvd":
            x = torch.linalg.pinv(A) @ b
        elif r == "syevd":
            ev, V = torch.linalg.eigh(A)
            # Match torch.linalg.pinv default: tol = rcond * max|ev| with
            # rcond = max(m,n) * eps (LAPACK convention).
            rcond = max(A.shape[0], A.shape[1]) * torch.finfo(A.dtype).eps
            ev_max = ev.abs().max().clamp(min=torch.finfo(A.dtype).tiny)
            tol = rcond * ev_max
            ev_inv = torch.where(
                ev.abs() > tol, 1.0 / ev, ev.new_zeros(1).expand_as(ev)
            )
            x = V @ (ev_inv.unsqueeze(1) * (V.T @ b))
        else:
            raise NotImplementedError(f"routine {r}")
        return x.squeeze(1) if b_was_1d else x
