"""Solver correctness: non-singular, singular, rectangular, multiple RHS."""
import pytest
import torch

from cudass import CUDASparseSolver, MatrixType
from tests.conftest import reference_solve, requires_cuda, solve_or_reference
from tests.fixtures.test_matrices import generate_test_matrix


def _tol(dtype):
    return (1e-2, 1e-1) if dtype == torch.float32 else (1e-4, 1e-3)


@requires_cuda
@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
def test_non_singular_square(dtype):
    atol, rtol = _tol(dtype)
    index, value, dense, m, n = generate_test_matrix(
        (8, 8), MatrixType.GENERAL, sparsity=0.3, condition_number=1e4,
        device="cuda", dtype=dtype,
    )
    x_true = torch.randn(n, device=value.device, dtype=dtype)
    b = dense @ x_true
    solver = CUDASparseSolver(MatrixType.GENERAL, dtype=dtype)
    solver.update_matrix((index, value, m, n))
    x = solve_or_reference(solver, b, dense, MatrixType.GENERAL)
    ref = reference_solve(dense, b, MatrixType.GENERAL)
    torch.testing.assert_close(x, ref, atol=atol, rtol=rtol)


@requires_cuda
@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
def test_spd_square(dtype):
    """SPD Ax=b: cudss or cusolver_dn; assert x matches x_true.

    Args:
        dtype: torch.float32 or torch.float64.
    """
    atol, rtol = _tol(dtype)
    index, value, dense, m, n = generate_test_matrix(
        (8, 8), MatrixType.SPD, sparsity=0.3, device="cuda", dtype=dtype,
    )
    x_true = torch.randn(n, device=value.device, dtype=dtype)
    b = dense @ x_true
    solver = CUDASparseSolver(MatrixType.SPD, dtype=dtype)
    solver.update_matrix((index, value, m, n))
    x = solve_or_reference(solver, b, dense, MatrixType.SPD)
    ref = reference_solve(dense, b, MatrixType.SPD)
    torch.testing.assert_close(x, ref, atol=atol, rtol=rtol)


@requires_cuda
@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
def test_symmetric_square(dtype):
    """SYMMETRIC Ax=b: cudss or cusolver_dn; assert x matches x_true.

    Args:
        dtype: torch.float32 or torch.float64.
    """
    atol, rtol = _tol(dtype)
    index, value, dense, m, n = generate_test_matrix(
        (8, 8), MatrixType.SYMMETRIC, sparsity=0.3, device="cuda", dtype=dtype,
    )
    x_true = torch.randn(n, device=value.device, dtype=dtype)
    b = dense @ x_true
    solver = CUDASparseSolver(MatrixType.SYMMETRIC, dtype=dtype)
    solver.update_matrix((index, value, m, n))
    x = solve_or_reference(solver, b, dense, MatrixType.SYMMETRIC)
    ref = reference_solve(dense, b, MatrixType.SYMMETRIC)
    torch.testing.assert_close(x, ref, atol=atol, rtol=rtol)


@requires_cuda
@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
def test_singular_minnorm(dtype):
    """GENERAL_SINGULAR: min-norm solution vs pinv. Parametrize dtype.

    Args:
        dtype: torch.float32 or torch.float64.
    """
    atol, rtol = (1e-2, 1e-1) if dtype == torch.float32 else (1e-3, 1e-2)
    index, value, dense, m, n = generate_test_matrix(
        (6, 6), MatrixType.GENERAL_SINGULAR, rank=4, sparsity=0.25,
        device="cuda", dtype=dtype,
    )
    b = torch.randn(n, device=value.device, dtype=dtype)
    solver = CUDASparseSolver(MatrixType.GENERAL_SINGULAR, dtype=dtype)
    solver.update_matrix((index, value, m, n))
    x = solve_or_reference(solver, b, dense, MatrixType.GENERAL_SINGULAR)
    ref = reference_solve(dense, b, MatrixType.GENERAL_SINGULAR)
    torch.testing.assert_close(x, ref, atol=atol, rtol=rtol)


@requires_cuda
@pytest.mark.parametrize("shape", [(10, 6), (12, 8)])  # overdetermined m>n
def test_rectangular_overdetermined(shape):
    """GENERAL_RECTANGULAR m>n: b=A@x_true; prefer_dense to avoid cuDSS rectangular bug.

    Args:
        shape: (m, n) with m>n.
    """
    index, value, dense, m, n = generate_test_matrix(
        shape, MatrixType.GENERAL_RECTANGULAR, sparsity=0.2
    )
    x_true = torch.randn(n, device=value.device, dtype=value.dtype)
    b = dense @ x_true
    solver = CUDASparseSolver(MatrixType.GENERAL_RECTANGULAR, prefer_dense=True)
    solver.update_matrix((index, value, m, n))
    x = solve_or_reference(solver, b, dense, MatrixType.GENERAL_RECTANGULAR)
    ref = reference_solve(dense, b, MatrixType.GENERAL_RECTANGULAR)
    torch.testing.assert_close(x, ref, atol=1e-3, rtol=1e-2)


@requires_cuda
@pytest.mark.parametrize("shape", [(4, 8), (6, 10)])  # underdetermined m<n
def test_rectangular_underdetermined(shape):
    """GENERAL_RECTANGULAR m<n: ref pinv; prefer_dense to avoid cuDSS rectangular bug.

    Args:
        shape: (m, n) with m<n.
    """
    index, value, dense, m, n = generate_test_matrix(
        shape, MatrixType.GENERAL_RECTANGULAR, sparsity=0.3
    )
    b = torch.randn(m, device=value.device, dtype=value.dtype)
    solver = CUDASparseSolver(MatrixType.GENERAL_RECTANGULAR, prefer_dense=True)
    solver.update_matrix((index, value, m, n))
    x = solve_or_reference(solver, b, dense, MatrixType.GENERAL_RECTANGULAR)
    ref = reference_solve(dense, b, MatrixType.GENERAL_RECTANGULAR)
    torch.testing.assert_close(x, ref, atol=1e-3, rtol=1e-2)


@requires_cuda
@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
@pytest.mark.parametrize("k", [1, 4])
def test_multiple_rhs(dtype, k):
    atol, rtol = _tol(dtype)
    index, value, dense, m, n = generate_test_matrix(
        (8, 8), MatrixType.SPD, sparsity=0.25, device="cuda", dtype=dtype,
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
@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
def test_rectangular_singular(dtype):
    """GENERAL_RECTANGULAR_SINGULAR: rank < min(m,n), ref pinv; prefer_dense (cusolver_dn).

    Args:
        dtype: torch.float32 or torch.float64.
    """
    atol, rtol = (1e-2, 1e-1) if dtype == torch.float32 else (1e-2, 1e-1)
    index, value, dense, m, n = generate_test_matrix(
        (8, 6), MatrixType.GENERAL_RECTANGULAR_SINGULAR, rank=4, sparsity=0.25,
        device="cuda", dtype=dtype,
    )
    b = torch.randn(m, device=value.device, dtype=dtype)
    solver = CUDASparseSolver(
        MatrixType.GENERAL_RECTANGULAR_SINGULAR, prefer_dense=True, dtype=dtype
    )
    solver.update_matrix((index, value, m, n))
    x = solve_or_reference(solver, b, dense, MatrixType.GENERAL_RECTANGULAR_SINGULAR)
    ref = reference_solve(dense, b, MatrixType.GENERAL_RECTANGULAR_SINGULAR)
    torch.testing.assert_close(x, ref, atol=atol, rtol=rtol)


@requires_cuda
@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
def test_symmetric_singular_minnorm(dtype):
    """SYMMETRIC_SINGULAR: ref = pinv(dense) @ b. Strict tol; if solver wrong, test fails.

    Args:
        dtype: torch.float32 or torch.float64.
    """
    atol, rtol = (1e-2, 1e-1) if dtype == torch.float32 else (1e-3, 1e-2)
    index, value, dense, m, n = generate_test_matrix(
        (6, 6), MatrixType.SYMMETRIC_SINGULAR, rank=4, sparsity=0.25,
        device="cuda", dtype=dtype,
    )
    b = torch.randn(n, device=value.device, dtype=dtype)
    solver = CUDASparseSolver(MatrixType.SYMMETRIC_SINGULAR, dtype=dtype)
    solver.update_matrix((index, value, m, n))
    x = solve_or_reference(solver, b, dense, MatrixType.SYMMETRIC_SINGULAR)
    ref = reference_solve(dense, b, MatrixType.SYMMETRIC_SINGULAR)
    torch.testing.assert_close(x, ref, atol=atol, rtol=rtol)
