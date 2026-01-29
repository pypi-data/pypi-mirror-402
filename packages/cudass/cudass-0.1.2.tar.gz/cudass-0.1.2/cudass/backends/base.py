# Placeholder for BackendBase - abstract interface
from abc import ABC, abstractmethod
from typing import Tuple

import torch


class BackendBase(ABC):
    """Abstract base for solver backends. To be implemented by cudss, cusolver_dn, cusolver_sp."""

    @property
    @abstractmethod
    def backend_name(self) -> str:
        """Backend identifier: 'cudss', 'cusolver_dn', or 'cusolver_sp'."""
        pass

    @property
    @abstractmethod
    def device(self) -> torch.device:
        pass

    @property
    @abstractmethod
    def dtype(self) -> torch.dtype:
        pass

    @abstractmethod
    def update_matrix(
        self,
        A_sparse: Tuple[torch.Tensor, torch.Tensor, int, int],
        structure_changed: bool = False,
    ) -> None:
        pass

    @abstractmethod
    def solve(self, b: torch.Tensor) -> torch.Tensor:
        pass
