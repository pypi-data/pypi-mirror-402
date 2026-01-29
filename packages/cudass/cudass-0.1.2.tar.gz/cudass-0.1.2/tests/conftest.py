# pytest configuration and fixtures
import os

import pytest
import torch

pytest.importorskip("torch")
cuda_available = torch.cuda.is_available()

requires_cuda = pytest.mark.skipif(not cuda_available, reason="CUDA not available")


# --- Fixtures ---


@pytest.fixture
def device():
    """CUDA device (cuda:0); skip when CUDA unavailable.

    Returns:
        torch.device: cuda or cuda:0.
    """
    if not cuda_available:
        pytest.skip("CUDA not available")
    return torch.device("cuda" if torch.cuda.device_count() == 1 else "cuda:0")


@pytest.fixture
def dtype():
    """Default dtype for tests; parametrization can override.

    Returns:
        torch.dtype: torch.float64.
    """
    return torch.float64


def _sparse_to_dense_available():
    """True if sparse_to_dense kernel is built and callable.

    Returns:
        bool: True if callable, else False.
    """
    try:
        from cudass.cuda.kernels import sparse_to_dense
        idx = torch.tensor([[0], [0]], device="cuda", dtype=torch.int64)
        val = torch.tensor([1.0], device="cuda", dtype=torch.float64)
        sparse_to_dense(idx, val, 1, 1)
        return True
    except (ImportError, RuntimeError):
        return False


def _cudss_available():
    """True if cudss_bindings can be imported.

    Returns:
        bool: True if importable, else False.
    """
    try:
        import cudass.cuda.bindings.cudss_bindings  # noqa: F401
        return True
    except ImportError:
        return False


@pytest.fixture
def requires_sparse_to_dense():
    """Skip if sparse_to_dense kernel is not built."""
    if not cuda_available:
        pytest.skip("CUDA not available")
    if not _sparse_to_dense_available():
        pytest.skip("sparse_to_dense kernel not built (need CUDA/nvcc at build)")


@pytest.fixture
def requires_cudss():
    """Skip if cudss_bindings cannot be imported."""
    if not cuda_available:
        pytest.skip("CUDA not available")
    if not _cudss_available():
        pytest.skip("cudss_bindings not available")


# --- Reference oracles (well-known correct solvers for test oracles) ---


def reference_solve(dense, b, matrix_type):
    """Reference solution: torch.linalg.solve for non-singular square;
    torch.linalg.pinv(dense) @ b for singular and rectangular.
    Tests compare solver.solve(b) to this; no tolerance relaxation.
    """
    from cudass.types import MatrixType

    square_nonsingular = (MatrixType.GENERAL, MatrixType.SYMMETRIC, MatrixType.SPD)
    if matrix_type in square_nonsingular:
        return torch.linalg.solve(dense, b).to(b.dtype)
    return (torch.linalg.pinv(dense) @ b).to(b.dtype)


def use_reference_solver():
    """True if CUDASS_TEST_USE_REFERENCE_SOLVER=1. When True, tests use reference_solve
    instead of solver.solve(b) to verify the test oracles and logic pass.

    Returns:
        bool: True when CUDASS_TEST_USE_REFERENCE_SOLVER=1.
    """
    return os.environ.get("CUDASS_TEST_USE_REFERENCE_SOLVER", "") == "1"


def solve_or_reference(solver, b, dense, matrix_type):
    """If CUDASS_TEST_USE_REFERENCE_SOLVER=1 return reference_solve(dense,b,matrix_type);
    else return solver.solve(b). Use to prove tests pass when the 'solver' is the reference.

    Args:
        solver: CUDASparseSolver instance (or reference substitute).
        b: RHS vector/matrix.
        dense: Dense representation of A for reference_solve.
        matrix_type: MatrixType for reference_solve.

    Returns:
        torch.Tensor: Solution from reference or solver.solve(b).

    Run: CUDASS_TEST_USE_REFERENCE_SOLVER=1 pytest tests/ -v
    (excluding test_solver_validation and test_built_extensions) to confirm all tests
    pass when the reference implementation is used as the solver; then the test
    oracles and logic are correct. Failures with the real solver indicate solver bugs.
    """
    if use_reference_solver():
        return reference_solve(dense, b, matrix_type)
    return solver.solve(b)
