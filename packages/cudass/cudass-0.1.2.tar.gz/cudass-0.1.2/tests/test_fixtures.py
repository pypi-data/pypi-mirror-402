"""Tests for generate_test_matrix contract and edge cases."""

import pytest
import torch

from cudass.types import MatrixType
from tests.conftest import requires_cuda
from tests.fixtures.test_matrices import generate_test_matrix

pytest.importorskip("torch")

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


@requires_cuda
@pytest.mark.parametrize("matrix_type,shape", [
    (MatrixType.SPD, (4, 4)),
    (MatrixType.SYMMETRIC, (5, 5)),
    (MatrixType.GENERAL, (6, 6)),
    (MatrixType.GENERAL_SINGULAR, (5, 5)),
    (MatrixType.SYMMETRIC_SINGULAR, (5, 5)),
    (MatrixType.GENERAL_RECTANGULAR, (8, 5)),
    (MatrixType.GENERAL_RECTANGULAR_SINGULAR, (5, 8)),
])
def test_generate_test_matrix_valid_per_type(matrix_type, shape):
    """For each MatrixType, one valid (shape, matrix_type) that respects square/rect.

    Args:
        matrix_type: MatrixType enum.
        shape: (m, n) shape.
    """
    index, value, dense, m, n = generate_test_matrix(shape, matrix_type, sparsity=0.2)
    assert index.shape[0] == 2 and index.dim() == 2
    assert index.shape[1] == value.shape[0]
    assert index.dtype == torch.int64
    assert value.dtype in (torch.float32, torch.float64)
    assert dense.shape == (m, n)
    assert m == shape[0] and n == shape[1]
    # dense[i,j]==value for each (i,j); symmetric may also store (j,i)
    for t in range(index.shape[1]):
        i, j = int(index[0, t].item()), int(index[1, t].item())
        assert abs(dense[i, j].item() - value[t].item()) < 1e-5


@requires_cuda
def test_generate_test_matrix_square_type_with_rectangular_shape_raises():
    """Square type with (3,5) -> ValueError."""
    with pytest.raises(ValueError, match="square"):
        generate_test_matrix((3, 5), MatrixType.GENERAL, sparsity=0.2)


@requires_cuda
def test_generate_test_matrix_rectangular_type_with_square_shape_raises():
    """Rectangular type with (4,4) -> ValueError."""
    with pytest.raises(ValueError, match="rectangular"):
        generate_test_matrix((4, 4), MatrixType.GENERAL_RECTANGULAR, sparsity=0.2)


@requires_cuda
@pytest.mark.parametrize("matrix_type", [MatrixType.GENERAL, MatrixType.SPD])
def test_generate_test_matrix_return_contract_index_value_dense(matrix_type):
    """Return contract: index [2, nnz], value [nnz], dense [m,n]; dense[indices] consistent.

    Args:
        matrix_type: MatrixType (GENERAL or SPD).
    """
    shape = (5, 5)
    index, value, dense, m, n = generate_test_matrix(shape, matrix_type, sparsity=0.25)
    assert index.shape[0] == 2
    assert value.shape[0] == index.shape[1]
    assert dense.shape == (m, n)
    # For symmetric types both (i,j) and (j,i) may exist; at least (i,j) should match
    for t in range(index.shape[1]):
        i, j = int(index[0, t].item()), int(index[1, t].item())
        assert 0 <= i < m and 0 <= j < n
        torch.testing.assert_close(dense[i, j], value[t], atol=1e-5, rtol=1e-5)


@requires_cuda
@pytest.mark.parametrize("sparsity", [0.01, 0.5])
def test_generate_test_matrix_sparsity(sparsity):
    """Optional: sparsity 0.01 and 0.5 produce valid matrices.

    Args:
        sparsity: Target sparsity.
    """
    index, value, dense, m, n = generate_test_matrix(
        (6, 6), MatrixType.GENERAL, sparsity=sparsity
    )
    assert index.shape[1] >= 1
    assert dense.shape == (m, n)


@requires_cuda
@pytest.mark.parametrize("condition_number", [1e2, 1e6])
def test_generate_test_matrix_condition_number(condition_number):
    """Optional: condition_number 1e2 and 1e6 produce valid matrices.

    Args:
        condition_number: Target condition number.
    """
    index, value, dense, m, n = generate_test_matrix(
        (6, 6), MatrixType.GENERAL, condition_number=condition_number, sparsity=0.2
    )
    assert dense.shape == (m, n)


@requires_cuda
def test_generate_test_matrix_rank_singular():
    """Optional: rank for singular types."""
    index, value, dense, m, n = generate_test_matrix(
        (6, 6), MatrixType.GENERAL_SINGULAR, rank=4, sparsity=0.2
    )
    assert dense.shape == (m, n)
