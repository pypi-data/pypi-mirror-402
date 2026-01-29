"""Unit tests for cudass.types: validate_matrix_type_shape, MatrixType, MatrixProperties."""

import pytest

from cudass.types import MatrixProperties, MatrixType, validate_matrix_type_shape

pytest.importorskip("torch")


# --- validate_matrix_type_shape ---

SQUARE_TYPES = [
    MatrixType.GENERAL,
    MatrixType.GENERAL_SINGULAR,
    MatrixType.SYMMETRIC,
    MatrixType.SYMMETRIC_SINGULAR,
    MatrixType.SPD,
]
RECT_TYPES = [
    MatrixType.GENERAL_RECTANGULAR,
    MatrixType.GENERAL_RECTANGULAR_SINGULAR,
]


@pytest.mark.parametrize("matrix_type", SQUARE_TYPES)
def test_validate_matrix_type_shape_square_ok(matrix_type):
    """Square types with m==n: no raise.

    Args:
        matrix_type: Square MatrixType.
    """
    validate_matrix_type_shape(matrix_type, 5, 5)


@pytest.mark.parametrize("matrix_type", SQUARE_TYPES)
def test_validate_matrix_type_shape_square_m_ne_n_raises(matrix_type):
    """Square types with m!=n: ValueError, message contains 'square'.

    Args:
        matrix_type: Square MatrixType.
    """
    with pytest.raises(ValueError, match="square"):
        validate_matrix_type_shape(matrix_type, 3, 5)


@pytest.mark.parametrize("matrix_type", RECT_TYPES)
def test_validate_matrix_type_shape_rectangular_ok(matrix_type):
    """Rectangular types with m!=n: no raise.

    Args:
        matrix_type: Rectangular MatrixType.
    """
    validate_matrix_type_shape(matrix_type, 10, 6)
    validate_matrix_type_shape(matrix_type, 6, 10)


@pytest.mark.parametrize("matrix_type", RECT_TYPES)
def test_validate_matrix_type_shape_rectangular_square_raises(matrix_type):
    """Rectangular types with m==n: ValueError, message contains 'rectangular'.

    Args:
        matrix_type: Rectangular MatrixType.
    """
    with pytest.raises(ValueError, match="rectangular"):
        validate_matrix_type_shape(matrix_type, 4, 4)


# --- MatrixType ---


def test_matrix_type_all_values_exist_and_distinct():
    """MatrixType: ensure all 7 values exist and are distinct."""
    expected = {
        MatrixType.GENERAL,
        MatrixType.GENERAL_SINGULAR,
        MatrixType.SYMMETRIC,
        MatrixType.SYMMETRIC_SINGULAR,
        MatrixType.SPD,
        MatrixType.GENERAL_RECTANGULAR,
        MatrixType.GENERAL_RECTANGULAR_SINGULAR,
    }
    assert set(MatrixType) == expected
    assert len(expected) == 7


# --- MatrixProperties ---


def test_matrix_properties_square():
    """(4,4): is_square True, is_overdetermined False, is_underdetermined False."""
    m, n = 4, 4
    p = MatrixProperties(
        shape=(m, n),
        is_square=(m == n),
        is_overdetermined=(m > n),
        is_underdetermined=(m < n),
    )
    assert p.is_square is True
    assert p.is_overdetermined is False
    assert p.is_underdetermined is False


def test_matrix_properties_overdetermined():
    """(5,3): is_square False, is_overdetermined True, is_underdetermined False."""
    m, n = 5, 3
    p = MatrixProperties(
        shape=(m, n),
        is_square=(m == n),
        is_overdetermined=(m > n),
        is_underdetermined=(m < n),
    )
    assert p.is_square is False
    assert p.is_overdetermined is True
    assert p.is_underdetermined is False


def test_matrix_properties_underdetermined():
    """(3,5): is_square False, is_overdetermined False, is_underdetermined True."""
    m, n = 3, 5
    p = MatrixProperties(
        shape=(m, n),
        is_square=(m == n),
        is_overdetermined=(m > n),
        is_underdetermined=(m < n),
    )
    assert p.is_square is False
    assert p.is_overdetermined is False
    assert p.is_underdetermined is True
