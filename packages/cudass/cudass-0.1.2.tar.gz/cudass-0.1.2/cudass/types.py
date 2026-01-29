"""Matrix type enumeration and properties for the CUDA sparse solver."""

from dataclasses import dataclass
from enum import Enum
from typing import Optional, Tuple


class MatrixType(Enum):
    """Matrix type for solver selection. Real matrices only (float32/float64).

    User must specify explicitly; no auto-inference. Shape: square types require
    m==n; GENERAL_RECTANGULAR and GENERAL_RECTANGULAR_SINGULAR require m!=n.
    """

    # Square, non-singular (m == n)
    GENERAL = "general"
    SYMMETRIC = "symmetric"
    SPD = "spd"
    # Square, singular — min-norm solution
    GENERAL_SINGULAR = "general_singular"
    SYMMETRIC_SINGULAR = "symmetric_singular"
    # Rectangular (m != n)
    GENERAL_RECTANGULAR = "general_rectangular"
    GENERAL_RECTANGULAR_SINGULAR = "general_rectangular_singular"


@dataclass
class MatrixProperties:
    """Validated or derived matrix properties (e.g. from shape). For validation only."""

    shape: Tuple[int, int]
    is_square: bool
    is_overdetermined: bool
    is_underdetermined: bool
    is_singular: Optional[bool] = None


def validate_matrix_type_shape(matrix_type: MatrixType, m: int, n: int) -> None:
    """Validate that matrix_type is consistent with shape (m, n).

    Args:
        matrix_type: The declared matrix type.
        m: Number of rows.
        n: Number of columns.

    Raises:
        ValueError: If square types have m != n or rectangular types have m == n.
    """
    square_types = {
        MatrixType.GENERAL,
        MatrixType.GENERAL_SINGULAR,
        MatrixType.SYMMETRIC,
        MatrixType.SYMMETRIC_SINGULAR,
        MatrixType.SPD,
    }
    rect_types = {
        MatrixType.GENERAL_RECTANGULAR,
        MatrixType.GENERAL_RECTANGULAR_SINGULAR,
    }
    if matrix_type in square_types and m != n:
        raise ValueError(
            f"MatrixType {matrix_type.name} requires square matrix (m==n); got m={m}, n={n}"
        )
    if matrix_type in rect_types and m == n:
        raise ValueError(
            f"MatrixType {matrix_type.name} requires rectangular matrix (m!=n); got m={m}, n={n}"
        )
