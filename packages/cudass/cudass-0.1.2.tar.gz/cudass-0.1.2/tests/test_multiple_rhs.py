"""Multiple RHS: k=1,4,16,64; float32; rectangular multi-RHS with cusolver_dn."""
import pytest
import torch

from cudass import CUDASparseSolver, MatrixType
from tests.conftest import reference_solve, requires_cuda, solve_or_reference
from tests.fixtures.test_matrices import generate_test_matrix


def _tol(dtype):
    return (1e-2, 1e-1) if dtype == torch.float32 else (1e-4, 1e-3)


@requires_cuda
@pytest.mark.parametrize("k", [1, 4, 16, 64])
@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
def test_multiple_rhs_k(k, dtype):
    atol, rtol = _tol(dtype)
    index, value, dense, m, n = generate_test_matrix(
        (12, 12), MatrixType.SPD, sparsity=0.2, device="cuda", dtype=dtype,
    )
    if k == 1:
        x_true = torch.randn(n, device=value.device, dtype=dtype)
        b = dense @ x_true
    else:
        x_true = torch.randn(n, k, device=value.device, dtype=dtype)
        b = dense @ x_true
    solver = CUDASparseSolver(MatrixType.SPD, dtype=dtype)
    solver.update_matrix((index, value, m, n))
    x = solve_or_reference(solver, b, dense, MatrixType.SPD)
    ref = reference_solve(dense, b, MatrixType.SPD)
    torch.testing.assert_close(x, ref, atol=atol, rtol=rtol)


@requires_cuda
def test_multiple_rhs_rectangular():
    """GENERAL_RECTANGULAR (12,8), b (m,k), prefer_dense; x_true (n,k), b=dense@x_true."""
    index, value, dense, m, n = generate_test_matrix(
        (12, 8), MatrixType.GENERAL_RECTANGULAR, sparsity=0.2
    )
    k = 4
    x_true = torch.randn(n, k, device=value.device, dtype=value.dtype)
    b = dense @ x_true
    solver = CUDASparseSolver(MatrixType.GENERAL_RECTANGULAR, prefer_dense=True)
    solver.update_matrix((index, value, m, n))
    x = solve_or_reference(solver, b, dense, MatrixType.GENERAL_RECTANGULAR)
    ref = reference_solve(dense, b, MatrixType.GENERAL_RECTANGULAR)
    torch.testing.assert_close(x, ref, atol=1e-2, rtol=1e-1)
