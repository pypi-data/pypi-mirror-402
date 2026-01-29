"""Refactorization: value-only, structure change, auto-detect, no-refactor same matrix."""
import torch

from cudass import CUDASparseSolver, MatrixType
from tests.conftest import reference_solve, requires_cuda, solve_or_reference
from tests.fixtures.test_matrices import generate_test_matrix


@requires_cuda
def test_value_only_update():
    index, value, dense, m, n = generate_test_matrix((6, 6), MatrixType.SPD, sparsity=0.3)
    value2 = value.clone() * 1.1
    x_true = torch.randn(n, device=value.device, dtype=value.dtype)
    dense2 = torch.zeros(m, n, device=dense.device, dtype=dense.dtype)
    dense2[index[0], index[1]] = value2
    b = dense2 @ x_true
    solver = CUDASparseSolver(MatrixType.SPD)
    solver.update_matrix((index, value, m, n))
    solver.update_matrix((index, value2, m, n), structure_changed=False)
    x = solve_or_reference(solver, b, dense2, MatrixType.SPD)
    ref = reference_solve(dense2, b, MatrixType.SPD)
    torch.testing.assert_close(x, ref, atol=1e-3, rtol=1e-2)


@requires_cuda
def test_structure_change():
    """Structure change: different (index,value); ref x_true from dense2 @ x_true = b."""
    index, value, dense, m, n = generate_test_matrix((6, 6), MatrixType.GENERAL, sparsity=0.25)
    solver = CUDASparseSolver(MatrixType.GENERAL)
    solver.update_matrix((index, value, m, n))
    # Second GENERAL matrix, different sparsity -> different structure; from fixture = non-singular
    index2, value2, dense2, m2, n2 = generate_test_matrix(
        (6, 6), MatrixType.GENERAL, sparsity=0.35
    )
    assert (m2, n2) == (m, n)
    solver.update_matrix((index2, value2, m2, n2), structure_changed=True)
    x_true = torch.randn(n2, device=value2.device, dtype=value2.dtype)
    b = dense2 @ x_true
    x = solve_or_reference(solver, b, dense2, MatrixType.GENERAL)
    ref = reference_solve(dense2, b, MatrixType.GENERAL)
    torch.testing.assert_close(x, ref, atol=1e-2, rtol=1e-1)


@requires_cuda
def test_auto_detect_structure_changed():
    """update_matrix(A), then A_vals_only with structure_changed=None -> value-only;
    then A_struct (different pattern, valid SPD) with structure_changed=None -> full refactor.
    Oracle: x_true for consistent Ax=b; dense from same (index,value) as passed to solver."""
    index, value, dense, m, n = generate_test_matrix((6, 6), MatrixType.SPD, sparsity=0.3)
    solver = CUDASparseSolver(MatrixType.SPD, prefer_dense=True)
    solver.update_matrix((index, value, m, n))
    # Value-only: same indices, different values; structure_changed=None -> value-only path
    value2 = value * 0.8 + 0.1
    dense2 = torch.zeros(m, n, device=dense.device, dtype=dense.dtype)
    dense2[index[0], index[1]] = value2
    solver.update_matrix((index, value2, m, n), structure_changed=None)
    x_true = torch.randn(n, device=value.device, dtype=value.dtype)
    b = dense2 @ x_true
    x = solve_or_reference(solver, b, dense2, MatrixType.SPD)
    ref = reference_solve(dense2, b, MatrixType.SPD)
    torch.testing.assert_close(x, ref, atol=1e-3, rtol=1e-2)
    # Structure change: different (index,value) from generate_test_matrix, still SPD
    index3, value3, dense3, m3, n3 = generate_test_matrix(
        (6, 6), MatrixType.SPD, sparsity=0.35
    )
    assert (m3, n3) == (m, n)
    solver.update_matrix((index3, value3, m3, n3), structure_changed=None)
    x_true3 = torch.randn(n3, device=value3.device, dtype=value3.dtype)
    b3 = dense3 @ x_true3
    x3 = solve_or_reference(solver, b3, dense3, MatrixType.SPD)
    ref3 = reference_solve(dense3, b3, MatrixType.SPD)
    torch.testing.assert_close(x3, ref3, atol=1e-3, rtol=1e-2)


@requires_cuda
def test_no_refactor_same_matrix():
    """update_matrix(A) twice with structure_changed=None -> no refactor; solve twice, same x."""
    index, value, dense, m, n = generate_test_matrix((6, 6), MatrixType.SPD, sparsity=0.3)
    solver = CUDASparseSolver(MatrixType.SPD, prefer_dense=True)
    solver.update_matrix((index, value, m, n))
    x_true = torch.randn(n, device=value.device, dtype=value.dtype)
    b = dense @ x_true
    x1 = solve_or_reference(solver, b, dense, MatrixType.SPD)
    solver.update_matrix((index, value, m, n), structure_changed=None)
    x2 = solve_or_reference(solver, b, dense, MatrixType.SPD)
    ref = reference_solve(dense, b, MatrixType.SPD)
    torch.testing.assert_close(x1, x2, atol=1e-9, rtol=1e-9)
    torch.testing.assert_close(x1, ref, atol=1e-3, rtol=1e-2)
