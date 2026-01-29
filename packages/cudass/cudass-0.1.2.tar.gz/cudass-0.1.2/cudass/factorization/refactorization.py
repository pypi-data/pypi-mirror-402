"""RefactorizationManager: should_refactorize (value-only vs structure change)."""

from typing import Optional, Tuple

import torch


class RefactorizationManager:
    """Determines if refactorization is needed and whether structure changed."""

    def should_refactorize(
        self,
        old_A: Optional[Tuple[torch.Tensor, torch.Tensor, int, int]],
        new_A: Tuple[torch.Tensor, torch.Tensor, int, int],
    ) -> Tuple[bool, bool]:
        """Return (needs_refactorization, structure_changed).

        - If old_A is None: (True, True).
        - If (m,n) or indices differ: (True, True).
        - If indices equal, values differ: (True, False).
        - If same structure and values: (False, False).

        Args:
            old_A: Previous (index, value, m, n) or None.
            new_A: Current (index, value, m, n).

        Returns:
            Tuple[bool, bool]: (needs_refactorization, structure_changed).
        """
        if old_A is None:
            return (True, True)
        (oi, ov, om, on), (ni, nv, nm, nn) = old_A, new_A
        if (om, on) != (nm, nn):
            return (True, True)
        if oi.shape != ni.shape or not torch.equal(oi, ni):
            return (True, True)
        if ov.shape == nv.shape and torch.equal(ov, nv):
            return (False, False)
        return (True, False)
