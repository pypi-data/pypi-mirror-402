"""Integration tests: solve workflows, use_cache=False, multi-solve, rectangular cusolver_dn."""

import pytest
import torch

from cudass import CUDASparseSolver, MatrixType
from tests.conftest import reference_solve, requires_cuda, solve_or_reference
from tests.fixtures.test_matrices import generate_test_matrix

pytest.importorskip("torch")


@requires_cuda
def test_same_A_many_b():
    """update_matrix(A) once, then solve(b1), solve(b2), ...; compare to references."""
    index, value, dense, m, n = generate_test_matrix((8, 8), MatrixType.SPD, sparsity=0.25)
    solver = CUDASparseSolver(MatrixType.SPD, prefer_dense=True)
    solver.update_matrix((index, value, m, n))
    for _ in range(3):
        x_true = torch.randn(n, device=value.device, dtype=value.dtype)
        b = dense @ x_true
        x = solve_or_reference(solver, b, dense, MatrixType.SPD)
        ref = reference_solve(dense, b, MatrixType.SPD)
        torch.testing.assert_close(x, ref, atol=1e-4, rtol=1e-3)


@requires_cuda
def test_use_cache_false():
    """use_cache=False: update_matrix(A), solve(b); update_matrix(A) again, solve; both correct."""
    index, value, dense, m, n = generate_test_matrix((6, 6), MatrixType.SPD, sparsity=0.3)
    solver = CUDASparseSolver(MatrixType.SPD, use_cache=False, prefer_dense=True)
    x_true = torch.randn(n, device=value.device, dtype=value.dtype)
    b = dense @ x_true
    solver.update_matrix((index, value, m, n))
    x1 = solve_or_reference(solver, b, dense, MatrixType.SPD)
    ref = reference_solve(dense, b, MatrixType.SPD)
    torch.testing.assert_close(x1, ref, atol=1e-3, rtol=1e-2)
    solver.update_matrix((index, value, m, n))
    x2 = solve_or_reference(solver, b, dense, MatrixType.SPD)
    torch.testing.assert_close(x2, ref, atol=1e-3, rtol=1e-2)


@requires_cuda
def test_rectangular_cusolver_dn_overdetermined():
    """GENERAL_RECTANGULAR (m>n), force_backend=cusolver_dn; b (m,); ref pinv; x (n,).
    Use pinv not lstsq: PyTorch lstsq on CUDA uses gels which only supports full-rank.
    """
    index, value, dense, m, n = generate_test_matrix(
        (10, 6), MatrixType.GENERAL_RECTANGULAR, sparsity=0.2
    )
    solver = CUDASparseSolver(MatrixType.GENERAL_RECTANGULAR, force_backend="cusolver_dn")
    solver.update_matrix((index, value, m, n))
    b = torch.randn(m, device=value.device, dtype=value.dtype)
    ref = reference_solve(dense, b, MatrixType.GENERAL_RECTANGULAR)
    x = solve_or_reference(solver, b, dense, MatrixType.GENERAL_RECTANGULAR)
    assert x.shape == (n,)
    torch.testing.assert_close(x, ref, atol=1e-2, rtol=1e-1)


@requires_cuda
def test_rectangular_cusolver_dn_underdetermined():
    """GENERAL_RECTANGULAR (m<n), force_backend=cusolver_dn; b (m,); ref pinv; x (n,)."""
    index, value, dense, m, n = generate_test_matrix(
        (6, 10), MatrixType.GENERAL_RECTANGULAR, sparsity=0.25
    )
    solver = CUDASparseSolver(MatrixType.GENERAL_RECTANGULAR, force_backend="cusolver_dn")
    solver.update_matrix((index, value, m, n))
    b = torch.randn(m, device=value.device, dtype=value.dtype)
    ref = reference_solve(dense, b, MatrixType.GENERAL_RECTANGULAR)
    x = solve_or_reference(solver, b, dense, MatrixType.GENERAL_RECTANGULAR)
    assert x.shape == (n,)
    torch.testing.assert_close(x, ref, atol=1e-2, rtol=1e-1)


@requires_cuda
def test_rectangular_singular_cusolver_dn():
    """GENERAL_RECTANGULAR_SINGULAR with force_backend='cusolver_dn'; b (m,) or (m,k); ref pinv."""
    index, value, dense, m, n = generate_test_matrix(
        (8, 6), MatrixType.GENERAL_RECTANGULAR_SINGULAR, rank=4, sparsity=0.25
    )
    solver = CUDASparseSolver(
        MatrixType.GENERAL_RECTANGULAR_SINGULAR, force_backend="cusolver_dn"
    )
    solver.update_matrix((index, value, m, n))
    b = torch.randn(m, device=value.device, dtype=value.dtype)
    ref = reference_solve(dense, b, MatrixType.GENERAL_RECTANGULAR_SINGULAR)
    x = solve_or_reference(solver, b, dense, MatrixType.GENERAL_RECTANGULAR_SINGULAR)
    assert x.shape == (n,)
    torch.testing.assert_close(x, ref, atol=1e-2, rtol=1e-1)

    b2 = torch.randn(m, 3, device=value.device, dtype=value.dtype)
    ref2 = reference_solve(dense, b2, MatrixType.GENERAL_RECTANGULAR_SINGULAR)
    x2 = solve_or_reference(solver, b2, dense, MatrixType.GENERAL_RECTANGULAR_SINGULAR)
    assert x2.shape == (n, 3)
    torch.testing.assert_close(x2, ref2, atol=1e-2, rtol=1e-1)
