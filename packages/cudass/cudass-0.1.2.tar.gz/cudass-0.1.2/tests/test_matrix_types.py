"""Test each MatrixType and backend selection."""
import pytest
import torch

from cudass import CUDASparseSolver, MatrixType
from cudass.backends.factory import select_backend
from tests.conftest import reference_solve, requires_cuda, solve_or_reference
from tests.fixtures.test_matrices import generate_test_matrix


@requires_cuda
@pytest.mark.parametrize("matrix_type,shape", [
    (MatrixType.SPD, (6, 6)),
    (MatrixType.SYMMETRIC, (6, 6)),
    (MatrixType.GENERAL, (6, 6)),
    (MatrixType.GENERAL_SINGULAR, (6, 6)),
    (MatrixType.SYMMETRIC_SINGULAR, (6, 6)),
    (MatrixType.GENERAL_RECTANGULAR, (8, 5)),
    (MatrixType.GENERAL_RECTANGULAR_SINGULAR, (5, 8)),
])
def test_matrix_type_runs(matrix_type, shape):
    index, value, dense, m, n = generate_test_matrix(shape, matrix_type, sparsity=0.2)
    # prefer_dense for rectangular to avoid cuDSS m!=n RHS bug
    rect = (MatrixType.GENERAL_RECTANGULAR, MatrixType.GENERAL_RECTANGULAR_SINGULAR)
    prefer_dense = matrix_type in rect
    solver = CUDASparseSolver(matrix_type, prefer_dense=prefer_dense)
    solver.update_matrix((index, value, m, n))
    x_true = torch.randn(n, device=value.device, dtype=value.dtype)
    b = dense @ x_true
    x = solve_or_reference(solver, b, dense, matrix_type)
    assert x.shape == x_true.shape
    assert x.dtype == x_true.dtype
    assert x.device == x_true.device


@requires_cuda
@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
def test_matrix_type_runs_float32_float64(dtype):
    """Parametrize dtype for at least one matrix type (SPD).

    Args:
        dtype: torch.float32 or torch.float64.
    """
    index, value, dense, m, n = generate_test_matrix(
        (6, 6), MatrixType.SPD, sparsity=0.2, device="cuda", dtype=dtype,
    )
    atol, rtol = (1e-2, 1e-1) if dtype == torch.float32 else (1e-4, 1e-3)
    solver = CUDASparseSolver(MatrixType.SPD, dtype=dtype)
    solver.update_matrix((index, value, m, n))
    x_true = torch.randn(n, device=value.device, dtype=dtype)
    b = dense @ x_true
    x = solve_or_reference(solver, b, dense, MatrixType.SPD)
    ref = reference_solve(dense, b, MatrixType.SPD)
    torch.testing.assert_close(x, ref, atol=atol, rtol=rtol)


@requires_cuda
def test_select_backend_spd():
    assert select_backend(MatrixType.SPD, (5, 5)) == "cudss"


@requires_cuda
def test_select_backend_singular():
    assert select_backend(MatrixType.GENERAL_SINGULAR, (5, 5)) == "cusolver_dn"
    assert select_backend(MatrixType.SYMMETRIC_SINGULAR, (5, 5)) == "cusolver_dn"
