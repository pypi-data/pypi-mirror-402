"""cuSolverSp backend - OOM fallback. Stub until Phase 3."""

from typing import Any, Optional, Tuple

import torch

from cudass.backends.base import BackendBase
from cudass.types import MatrixType


class CusolverSpBackend(BackendBase):
    """Stub: to be implemented in cusolver_sp_backend (Phase 3)."""

    @property
    def backend_name(self) -> str:
        return "cusolver_sp"

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
        raise NotImplementedError("CusolverSpBackend not yet implemented")

    def solve(self, b: torch.Tensor) -> torch.Tensor:
        raise NotImplementedError("CusolverSpBackend not yet implemented")
