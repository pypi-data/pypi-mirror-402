"""Solver input validation and error paths: update_matrix, solve, CUDASparseSolver(no CUDA)."""

import pytest
import torch

from cudass import CUDASparseSolver, MatrixType
from tests.conftest import requires_cuda
from tests.fixtures.test_matrices import generate_test_matrix

pytest.importorskip("torch")


# --- solve before update_matrix ---


@requires_cuda
def test_solve_before_update_matrix_raises():
    """solve before update_matrix -> ValueError with 'update_matrix' in message."""
    solver = CUDASparseSolver(MatrixType.GENERAL)
    b = torch.randn(8, device="cuda", dtype=torch.float64)
    with pytest.raises(ValueError, match="update_matrix"):
        solver.solve(b)


# --- update_matrix(A_sparse) validation ---


def _valid_A(device="cuda", m=4, n=4, nnz=4):
    idx = torch.tensor([[0, 1, 2, 3][:nnz], [0, 1, 2, 3][:nnz]], device=device, dtype=torch.int64)
    val = torch.ones(nnz, device=device, dtype=torch.float64)
    return (idx, val, m, n)


@requires_cuda
def test_update_matrix_index_not_2_nnz():
    """index not [2, nnz] (e.g. [3, nnz]) -> ValueError."""
    idx = torch.tensor([[0, 1, 2], [0, 1, 2], [0, 0, 0]], device="cuda", dtype=torch.int64)
    val = torch.ones(3, device="cuda", dtype=torch.float64)
    solver = CUDASparseSolver(MatrixType.GENERAL)
    with pytest.raises(ValueError, match="index must be \\[2, nnz\\]"):
        solver.update_matrix((idx, val, 4, 4))


@requires_cuda
def test_update_matrix_value_shape_mismatch():
    """[2, nnz] but value.shape[0] != nnz -> ValueError."""
    idx = torch.tensor([[0, 1], [0, 1]], device="cuda", dtype=torch.int64)
    val = torch.ones(5, device="cuda", dtype=torch.float64)  # 5 != 2
    solver = CUDASparseSolver(MatrixType.GENERAL)
    with pytest.raises(ValueError, match="value must be"):
        solver.update_matrix((idx, val, 4, 4))


@requires_cuda
def test_update_matrix_index_dtype_not_int64():
    """index.dtype not torch.int64 -> ValueError."""
    idx = torch.tensor([[0, 1], [0, 1]], device="cuda", dtype=torch.int32)
    val = torch.ones(2, device="cuda", dtype=torch.float64)
    solver = CUDASparseSolver(MatrixType.GENERAL)
    with pytest.raises(ValueError, match="index must be torch.int64"):
        solver.update_matrix((idx, val, 4, 4))


@requires_cuda
def test_update_matrix_value_dtype_not_float():
    """value.dtype not float32/float64 -> ValueError."""
    idx = torch.tensor([[0, 1], [0, 1]], device="cuda", dtype=torch.int64)
    val = torch.ones(2, device="cuda", dtype=torch.float16)
    solver = CUDASparseSolver(MatrixType.GENERAL)
    with pytest.raises(ValueError, match="value must be torch.float32 or torch.float64"):
        solver.update_matrix((idx, val, 4, 4))


@requires_cuda
def test_update_matrix_index_on_cpu():
    """index on CPU -> ValueError."""
    idx = torch.tensor([[0, 1], [0, 1]], device="cpu", dtype=torch.int64)
    val = torch.ones(2, device="cuda", dtype=torch.float64)
    solver = CUDASparseSolver(MatrixType.GENERAL)
    with pytest.raises(ValueError, match="index and value must be on CUDA"):
        solver.update_matrix((idx, val, 4, 4))


@requires_cuda
def test_update_matrix_value_on_cpu():
    """value on CPU -> ValueError."""
    idx = torch.tensor([[0, 1], [0, 1]], device="cuda", dtype=torch.int64)
    val = torch.ones(2, device="cpu", dtype=torch.float64)
    solver = CUDASparseSolver(MatrixType.GENERAL)
    with pytest.raises(ValueError, match="index and value must be on CUDA"):
        solver.update_matrix((idx, val, 4, 4))


@requires_cuda
def test_update_matrix_m_zero():
    """m<=0 -> ValueError."""
    idx, val, _, n = _valid_A(m=4, n=4)
    solver = CUDASparseSolver(MatrixType.GENERAL)
    with pytest.raises(ValueError, match="m and n must be positive"):
        solver.update_matrix((idx, val, 0, n))


@requires_cuda
def test_update_matrix_n_zero():
    """n<=0 -> ValueError."""
    idx, val, m, _ = _valid_A(m=4, n=4)
    solver = CUDASparseSolver(MatrixType.GENERAL)
    with pytest.raises(ValueError, match="m and n must be positive"):
        solver.update_matrix((idx, val, m, 0))


@requires_cuda
def test_update_matrix_general_with_rectangular_shape():
    """matrix_type GENERAL with (3,5) -> ValueError (square required)."""
    idx = torch.tensor([[0, 1, 2], [0, 1, 2]], device="cuda", dtype=torch.int64)
    value = torch.ones(3, device="cuda", dtype=torch.float64)
    solver = CUDASparseSolver(MatrixType.GENERAL)
    with pytest.raises(ValueError, match="square"):
        solver.update_matrix((idx, value, 3, 5))


@requires_cuda
def test_update_matrix_general_rectangular_with_square_shape():
    """matrix_type GENERAL_RECTANGULAR with (4,4) -> ValueError (rectangular required)."""
    idx = torch.tensor([[0, 1, 2, 3], [0, 1, 2, 3]], device="cuda", dtype=torch.int64)
    value = torch.ones(4, device="cuda", dtype=torch.float64)
    solver = CUDASparseSolver(MatrixType.GENERAL_RECTANGULAR)
    with pytest.raises(ValueError, match="rectangular"):
        solver.update_matrix((idx, value, 4, 4))


# --- solve(b) validation ---


@requires_cuda
def test_solve_b_0d():
    """b 0-d -> ValueError."""
    index, value, _, m, n = generate_test_matrix((4, 4), MatrixType.GENERAL, sparsity=0.3)
    solver = CUDASparseSolver(MatrixType.GENERAL)
    solver.update_matrix((index, value, m, n))
    b = torch.tensor(1.0, device="cuda", dtype=torch.float64)
    with pytest.raises(ValueError, match="1D \\[m\\] or 2D \\[m, k\\]"):
        solver.solve(b)


@requires_cuda
def test_solve_b_3d():
    """b 3-d -> ValueError."""
    index, value, dense, m, n = generate_test_matrix((4, 4), MatrixType.GENERAL, sparsity=0.3)
    solver = CUDASparseSolver(MatrixType.GENERAL)
    solver.update_matrix((index, value, m, n))
    b = torch.randn(m, 2, 2, device="cuda", dtype=torch.float64)
    with pytest.raises(ValueError, match="1D \\[m\\] or 2D \\[m, k\\]"):
        solver.solve(b)


@requires_cuda
def test_solve_b_shape0_ne_m_1d():
    """b 1d with shape[0] != m -> ValueError."""
    index, value, dense, m, n = generate_test_matrix((4, 4), MatrixType.GENERAL, sparsity=0.3)
    solver = CUDASparseSolver(MatrixType.GENERAL)
    solver.update_matrix((index, value, m, n))
    b = torch.randn(m + 1, device="cuda", dtype=torch.float64)
    with pytest.raises(ValueError, match="m"):
        solver.solve(b)


@requires_cuda
def test_solve_b_shape0_ne_m_2d():
    """b 2d with shape[0] != m -> ValueError."""
    index, value, dense, m, n = generate_test_matrix((4, 4), MatrixType.GENERAL, sparsity=0.3)
    solver = CUDASparseSolver(MatrixType.GENERAL)
    solver.update_matrix((index, value, m, n))
    b = torch.randn(m + 1, 2, device="cuda", dtype=torch.float64)
    with pytest.raises(ValueError, match="m"):
        solver.solve(b)


@requires_cuda
def test_solve_b_dtype_not_float():
    """b.dtype not float32/float64 -> ValueError."""
    index, value, dense, m, n = generate_test_matrix((4, 4), MatrixType.GENERAL, sparsity=0.3)
    solver = CUDASparseSolver(MatrixType.GENERAL)
    solver.update_matrix((index, value, m, n))
    b = torch.randn(m, device="cuda", dtype=torch.float16)
    with pytest.raises(ValueError, match="b must be torch.float32 or torch.float64"):
        solver.solve(b)


@requires_cuda
def test_solve_b_on_cpu():
    """b on CPU -> ValueError."""
    index, value, dense, m, n = generate_test_matrix((4, 4), MatrixType.GENERAL, sparsity=0.3)
    solver = CUDASparseSolver(MatrixType.GENERAL)
    solver.update_matrix((index, value, m, n))
    b = torch.randn(m, device="cpu", dtype=torch.float64)
    with pytest.raises(ValueError, match="b must be on CUDA"):
        solver.solve(b)


@requires_cuda
def test_solve_b_device_mismatch():
    """b.device != solver device (when solver has device) -> ValueError."""
    index, value, dense, m, n = generate_test_matrix(
        (4, 4), MatrixType.GENERAL, sparsity=0.3, device="cuda:0"
    )
    solver = CUDASparseSolver(MatrixType.GENERAL, device=torch.device("cuda:0"))
    solver.update_matrix((index, value, m, n))
    if torch.cuda.device_count() >= 2:
        b = torch.randn(m, device="cuda:1", dtype=torch.float64)
    else:
        # One GPU: use a tensor-like with .device = cuda:1 to hit the mismatch check.
        b = torch.randn(m, device="cuda:0", dtype=torch.float64)
        base = torch.randn(m, device="cuda:0", dtype=torch.float64)
        b = type("_B", (), {"dim": lambda self: 1, "shape": (m,), "dtype": base.dtype,
                            "is_cuda": True, "device": torch.device("cuda:1")})()
    with pytest.raises(ValueError, match="same device"):
        solver.solve(b)


# --- CUDASparseSolver when CUDA not available ---


def test_solver_raises_when_cuda_unavailable():
    """CUDASparseSolver when torch.cuda.is_available() is False -> RuntimeError."""
    import unittest.mock as mock
    with mock.patch("torch.cuda.is_available", return_value=False):
        with pytest.raises(RuntimeError, match="CUDA is not available"):
            CUDASparseSolver(MatrixType.GENERAL)
