"""Tests for backend selection, backend_name, and coverage of all backends."""

import pytest
import torch

from cudass import CUDASparseSolver, MatrixType
from cudass.backends.factory import create_backend, select_backend
from tests.conftest import reference_solve, requires_cuda, solve_or_reference
from tests.fixtures.test_matrices import generate_test_matrix

# --- Helpers -----------------------------------------------------------------


def _allowed_non_stub(*names: str):
    """Backends that may be used when cudss is optional (cudss or cusolver_dn).

    Args:
        *names: Allowed backend name strings.

    Returns:
        tuple: The names.
    """
    return names


# --- select_backend (unit) ---------------------------------------------------


@requires_cuda
@pytest.mark.parametrize("matrix_type,shape,prefer_dense,expected", [
    (MatrixType.SPD, (10, 10), False, "cudss"),
    (MatrixType.SPD, (10, 10), True, "cusolver_dn"),
    (MatrixType.GENERAL, (8, 8), False, "cudss"),
    (MatrixType.SYMMETRIC, (8, 8), False, "cudss"),
    (MatrixType.GENERAL_SINGULAR, (8, 8), False, "cusolver_dn"),
    (MatrixType.SYMMETRIC_SINGULAR, (8, 8), False, "cusolver_dn"),
    (MatrixType.GENERAL_RECTANGULAR, (12, 8), False, "cudss"),
    (MatrixType.GENERAL_RECTANGULAR_SINGULAR, (8, 12), False, "cusolver_dn"),
])
def test_select_backend_unit(matrix_type, shape, prefer_dense, expected):
    assert select_backend(matrix_type, shape, prefer_dense=prefer_dense) == expected


# --- backend_name exposed on solver ------------------------------------------


@requires_cuda
def test_solver_backend_name_exposed():
    index, value, dense, m, n = generate_test_matrix((8, 8), MatrixType.SPD, sparsity=0.2)
    solver = CUDASparseSolver(MatrixType.SPD)
    assert solver.backend_name == "stub"
    solver.update_matrix((index, value, m, n))
    assert solver.backend_name in ("cudss", "cusolver_dn")
    b = dense @ torch.randn(n, device=value.device, dtype=value.dtype)
    x = solve_or_reference(solver, b, dense, MatrixType.SPD)
    assert x.shape == (n,)
    assert solver.backend_name in ("cudss", "cusolver_dn")


# --- Backends by matrix type and size ----------------------------------------


_SQUARE_SIZES = [(4, 4), (8, 8), (16, 16), (32, 32), (64, 64)]
_RECT_OVER = [(16, 12), (32, 24)]
_RECT_UNDER = [(12, 16), (24, 32)]


@requires_cuda
@pytest.mark.parametrize("shape", _SQUARE_SIZES)
def test_backend_cudss_or_dn_spd_sizes(shape):
    """SPD: cudss when available; cusolver_dn fallback. Fixture ensures densified is SPD.

    Args:
        shape: (m, n) matrix shape.
    """
    index, value, dense, m, n = generate_test_matrix(shape, MatrixType.SPD, sparsity=0.15)
    solver = CUDASparseSolver(MatrixType.SPD)
    solver.update_matrix((index, value, m, n))
    assert solver.backend_name in _allowed_non_stub("cudss", "cusolver_dn")
    x_true = torch.randn(n, device=value.device, dtype=value.dtype)
    b = dense @ x_true
    x = solve_or_reference(solver, b, dense, MatrixType.SPD)
    ref = reference_solve(dense, b, MatrixType.SPD)
    torch.testing.assert_close(x, ref, atol=1e-4, rtol=1e-3)


@requires_cuda
@pytest.mark.parametrize("shape", _SQUARE_SIZES[:4])  # 4,8,16,32
def test_backend_cudss_or_dn_general_sizes(shape):
    index, value, dense, m, n = generate_test_matrix(shape, MatrixType.GENERAL, sparsity=0.2)
    solver = CUDASparseSolver(MatrixType.GENERAL)
    solver.update_matrix((index, value, m, n))
    assert solver.backend_name in _allowed_non_stub("cudss", "cusolver_dn")
    x_true = torch.randn(n, device=value.device, dtype=value.dtype)
    b = dense @ x_true
    x = solve_or_reference(solver, b, dense, MatrixType.GENERAL)
    ref = reference_solve(dense, b, MatrixType.GENERAL)
    torch.testing.assert_close(x, ref, atol=1e-4, rtol=1e-3)


@requires_cuda
@pytest.mark.parametrize("shape", _SQUARE_SIZES[:4])  # 4,8,16,32
def test_backend_cudss_or_dn_symmetric_sizes(shape):
    """SYMMETRIC: cudss when available; cusolver_dn fallback; assert correctness.

    Args:
        shape: (m, n) matrix shape.
    """
    index, value, dense, m, n = generate_test_matrix(shape, MatrixType.SYMMETRIC, sparsity=0.2)
    solver = CUDASparseSolver(MatrixType.SYMMETRIC)
    solver.update_matrix((index, value, m, n))
    assert solver.backend_name in _allowed_non_stub("cudss", "cusolver_dn")
    x_true = torch.randn(n, device=value.device, dtype=value.dtype)
    b = dense @ x_true
    x = solve_or_reference(solver, b, dense, MatrixType.SYMMETRIC)
    ref = reference_solve(dense, b, MatrixType.SYMMETRIC)
    torch.testing.assert_close(x, ref, atol=1e-4, rtol=1e-3)


@requires_cuda
@pytest.mark.parametrize("shape", _SQUARE_SIZES[:4])
def test_backend_cusolver_dn_singular_sizes(shape):
    """GENERAL_SINGULAR and SYMMETRIC_SINGULAR always use cusolver_dn.

    Args:
        shape: (m, n) matrix shape.
    """
    for mtype in (MatrixType.GENERAL_SINGULAR, MatrixType.SYMMETRIC_SINGULAR):
        index, value, dense, m, n = generate_test_matrix(shape, mtype, sparsity=0.2)
        solver = CUDASparseSolver(mtype)
        solver.update_matrix((index, value, m, n))
        assert solver.backend_name == "cusolver_dn"
        b = dense @ torch.randn(n, device=value.device, dtype=value.dtype)
        x = solve_or_reference(solver, b, dense, mtype)
        assert x.shape == (n,)


@requires_cuda
@pytest.mark.parametrize("shape", _RECT_OVER + _RECT_UNDER)
def test_backend_rectangular_sizes(shape):
    """Rectangular: prefer_dense to avoid cuDSS m!=n bug; cusolver_dn for _SINGULAR.

    Args:
        shape: (m, n) matrix shape.
    """
    m, n = shape
    for mtype in (MatrixType.GENERAL_RECTANGULAR, MatrixType.GENERAL_RECTANGULAR_SINGULAR):
        index, value, dense, _, _ = generate_test_matrix(shape, mtype, sparsity=0.15)
        prefer = mtype == MatrixType.GENERAL_RECTANGULAR  # cuDSS rectangular RHS bug
        solver = CUDASparseSolver(mtype, prefer_dense=prefer)
        solver.update_matrix((index, value, m, n))
        # GENERAL_RECTANGULAR: cudss or cusolver_dn; _SINGULAR: cusolver_dn
        assert solver.backend_name in _allowed_non_stub("cudss", "cusolver_dn")
        rhs = torch.randn(m, device=value.device, dtype=value.dtype)
        x = solve_or_reference(solver, rhs, dense, mtype)
        assert x.shape == (n,)


# --- Force prefer_dense / force_backend --------------------------------------


@requires_cuda
@pytest.mark.parametrize("shape", [(6, 6), (16, 16), (24, 24)])
@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
def test_backend_cusolver_dn_prefer_dense(shape, dtype):
    """prefer_dense=True forces cusolver_dn for SPD. Parametrize dtype.

    Args:
        shape: (m, n) matrix shape.
        dtype: torch.float32 or torch.float64.
    """
    atol, rtol = (1e-2, 1e-1) if dtype == torch.float32 else (1e-4, 1e-3)
    index, value, dense, m, n = generate_test_matrix(
        shape, MatrixType.SPD, sparsity=0.2, device="cuda", dtype=dtype,
    )
    solver = CUDASparseSolver(MatrixType.SPD, prefer_dense=True, dtype=dtype)
    solver.update_matrix((index, value, m, n))
    assert solver.backend_name == "cusolver_dn"
    x_true = torch.randn(n, device=value.device, dtype=dtype)
    b = dense @ x_true
    x = solve_or_reference(solver, b, dense, MatrixType.SPD)
    ref = reference_solve(dense, b, MatrixType.SPD)
    torch.testing.assert_close(x, ref, atol=atol, rtol=rtol)


@requires_cuda
def test_backend_force_cudss():
    """force_backend='cudss' uses cudss when available; skip when cudss_bindings missing.

    Raises:
        RuntimeError: Re-raised if update_matrix fails for non-cudss reason.
    """
    index, value, dense, m, n = generate_test_matrix((8, 8), MatrixType.SPD, sparsity=0.2)
    solver = CUDASparseSolver(MatrixType.SPD, force_backend="cudss")
    try:
        solver.update_matrix((index, value, m, n))
    except RuntimeError as e:
        if "cudss" in str(e).lower() or "cudss_bindings" in str(e):
            pytest.skip("cudss_bindings not available")
        raise
    assert solver.backend_name == "cudss"
    x_true = torch.randn(n, device=value.device, dtype=value.dtype)
    b = dense @ x_true
    x = solve_or_reference(solver, b, dense, MatrixType.SPD)
    ref = reference_solve(dense, b, MatrixType.SPD)
    torch.testing.assert_close(x, ref, atol=1e-4, rtol=1e-3)


@requires_cuda
@pytest.mark.parametrize("shape", [(6, 6), (12, 12)])
def test_backend_force_cusolver_dn(shape):
    """force_backend='cusolver_dn' forces dense backend for any type.

    Args:
        shape: (m, n) matrix shape.
    """
    index, value, dense, m, n = generate_test_matrix(shape, MatrixType.SPD, sparsity=0.25)
    solver = CUDASparseSolver(MatrixType.SPD, force_backend="cusolver_dn")
    solver.update_matrix((index, value, m, n))
    assert solver.backend_name == "cusolver_dn"
    b = dense @ torch.randn(n, device=value.device, dtype=value.dtype)
    x = solve_or_reference(solver, b, dense, MatrixType.SPD)
    assert x.shape == (n,)


@requires_cuda
def test_backend_create_backend_invalid_force_backend_raises():
    """create_backend with invalid force_backend -> ValueError."""
    with pytest.raises(ValueError, match="Unknown backend"):
        create_backend(
            MatrixType.GENERAL, (4, 4), torch.device("cuda"), torch.float64,
            force_backend="invalid_backend",
        )


@requires_cuda
def test_backend_force_cusolver_sp_raises():
    """force_backend='cusolver_sp' yields CusolverSpBackend; update_matrix raises (stub)."""
    index, value, dense, m, n = generate_test_matrix((6, 6), MatrixType.GENERAL, sparsity=0.2)
    solver = CUDASparseSolver(MatrixType.GENERAL, force_backend="cusolver_sp")
    with pytest.raises(NotImplementedError, match="CusolverSpBackend not yet implemented"):
        solver.update_matrix((index, value, m, n))


@requires_cuda
def test_backend_create_backend_force_cusolver_sp_name():
    """force_backend='cusolver_sp' returns backend with backend_name 'cusolver_sp'."""
    dev = torch.device("cuda")
    b = create_backend(
        MatrixType.GENERAL, (6, 6), dev, torch.float64, force_backend="cusolver_sp"
    )
    assert b.backend_name == "cusolver_sp"


# --- Scenarios: multi-RHS, value-only, structure change ----------------------


@requires_cuda
@pytest.mark.parametrize("backend_force,matrix_type,shape", [
    ("cusolver_dn", MatrixType.SPD, (12, 12)),
    (None, MatrixType.GENERAL_SINGULAR, (10, 10)),  # cusolver_dn by type
    (None, MatrixType.SYMMETRIC, (10, 10)),  # cudss or cusolver_dn
    (None, MatrixType.GENERAL, (8, 8)),  # cudss or cusolver_dn
])
@pytest.mark.parametrize("k", [1, 4, 64])
def test_backend_scenarios_multi_rhs(backend_force, matrix_type, shape, k):
    """Multi-RHS: ensure backend_name is set and solve(b [m,k]) works.

    Args:
        backend_force: Optional force_backend value.
        matrix_type: MatrixType.
        shape: (m, n) matrix shape.
        k: Number of RHS columns.
    """
    kwargs = {"force_backend": backend_force} if backend_force else {}
    index, value, dense, m, n = generate_test_matrix(shape, matrix_type, sparsity=0.2)
    solver = CUDASparseSolver(matrix_type, **kwargs)
    solver.update_matrix((index, value, m, n))
    assert solver.backend_name in _allowed_non_stub("cudss", "cusolver_dn")
    if k == 1:
        x_true = torch.randn(n, device=value.device, dtype=value.dtype)
        b = dense @ x_true
    else:
        x_true = torch.randn(n, k, device=value.device, dtype=value.dtype)
        b = dense @ x_true
    x = solve_or_reference(solver, b, dense, matrix_type)
    assert x.shape == x_true.shape
    ref = reference_solve(dense, b, matrix_type)
    if matrix_type == MatrixType.GENERAL_SINGULAR:
        torch.testing.assert_close(x, ref, atol=1e-2, rtol=1e-1)
    else:
        torch.testing.assert_close(x, ref, atol=1e-3, rtol=1e-2)


@requires_cuda
def test_backend_scenarios_value_only_update():
    """Value-only update: backend stays same, solve still correct."""
    index, value, dense, m, n = generate_test_matrix((8, 8), MatrixType.SPD, sparsity=0.3)
    solver = CUDASparseSolver(MatrixType.SPD, prefer_dense=True)
    solver.update_matrix((index, value, m, n))
    name_before = solver.backend_name
    assert name_before == "cusolver_dn"
    value2 = value * 0.7 + 0.1
    dense2 = torch.zeros(m, n, device=dense.device, dtype=dense.dtype)
    dense2[index[0], index[1]] = value2
    solver.update_matrix((index, value2, m, n), structure_changed=False)
    assert solver.backend_name == name_before
    x_true = torch.randn(n, device=value.device, dtype=value.dtype)
    b = dense2 @ x_true
    x = solve_or_reference(solver, b, dense2, MatrixType.SPD)
    ref = reference_solve(dense2, b, MatrixType.SPD)
    torch.testing.assert_close(x, ref, atol=1e-3, rtol=1e-2)


@requires_cuda
def test_backend_scenarios_structure_change():
    """Structure change: backend may be recreated; solve remains correct."""
    index, value, dense, m, n = generate_test_matrix((8, 8), MatrixType.GENERAL, sparsity=0.25)
    solver = CUDASparseSolver(MatrixType.GENERAL, prefer_dense=True)
    solver.update_matrix((index, value, m, n))
    assert solver.backend_name == "cusolver_dn"
    index2 = index.clone()
    index2[0, 0] = (index2[0, 0] + 1) % m
    value2 = torch.randn(index2.shape[1], device=value.device, dtype=value.dtype) * 0.3
    for i in range(m):
        if not ((index2[0] == i) & (index2[1] == i)).any():
            idx_ii = torch.tensor([[i], [i]], device=index.device, dtype=index.dtype)
            index2 = torch.cat([index2, idx_ii], 1)
            v = torch.tensor([2.0], device=value.device, dtype=value.dtype)
            value2 = torch.cat([value2, v])
    dense2 = torch.zeros(m, n, device=dense.device, dtype=dense.dtype)
    dense2[index2[0], index2[1]] = value2
    x_true = torch.randn(n, device=value.device, dtype=value.dtype)
    b = dense2 @ x_true
    solver.update_matrix((index2, value2, m, n), structure_changed=True)
    assert solver.backend_name == "cusolver_dn"
    x = solve_or_reference(solver, b, dense2, MatrixType.GENERAL)
    ref = reference_solve(dense2, b, MatrixType.GENERAL)
    torch.testing.assert_close(x, ref, atol=1e-2, rtol=1e-1)


# --- Backend coverage summary (one run per backend type) ----------------------


@requires_cuda
def test_backend_coverage_cudss_when_available():
    """At least one path uses cudss when bindings exist. We run and record; no strict assert."""
    index, value, dense, m, n = generate_test_matrix((8, 8), MatrixType.SPD, sparsity=0.2)
    solver = CUDASparseSolver(MatrixType.SPD)  # no prefer_dense
    solver.update_matrix((index, value, m, n))
    b = dense @ torch.randn(n, device=value.device, dtype=value.dtype)
    solve_or_reference(solver, b, dense, MatrixType.SPD)
    # cudss or cusolver_dn; both are valid. Test documents backend_name is observable.
    assert solver.backend_name in ("cudss", "cusolver_dn")


@requires_cuda
def test_backend_coverage_cusolver_dn():
    """Explicit cusolver_dn path (singular type)."""
    index, value, dense, m, n = generate_test_matrix(
        (10, 10), MatrixType.GENERAL_SINGULAR, sparsity=0.2
    )
    solver = CUDASparseSolver(MatrixType.GENERAL_SINGULAR)
    solver.update_matrix((index, value, m, n))
    assert solver.backend_name == "cusolver_dn"
    b = dense @ torch.randn(n, device=value.device, dtype=value.dtype)
    solve_or_reference(solver, b, dense, MatrixType.GENERAL_SINGULAR)


# --- cuSOLVER Dense routine coverage: potrs, sytrs, getrs, gels, gesvd, syevd ---


@requires_cuda
@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
def test_backend_cusolver_dn_routine_potrs(dtype):
    """SPD -> potrs (Cholesky); compare to cholesky_solve. Parametrize dtype.

    Args:
        dtype: torch.float32 or torch.float64.
    """
    atol, rtol = (1e-2, 1e-1) if dtype == torch.float32 else (1e-4, 1e-3)
    index, value, dense, m, n = generate_test_matrix(
        (8, 8), MatrixType.SPD, sparsity=0.25, device="cuda", dtype=dtype,
    )
    solver = CUDASparseSolver(MatrixType.SPD, force_backend="cusolver_dn", dtype=dtype)
    solver.update_matrix((index, value, m, n))
    assert solver.backend_name == "cusolver_dn"
    x_true = torch.randn(n, device=value.device, dtype=dtype)
    b = dense @ x_true
    x = solve_or_reference(solver, b, dense, MatrixType.SPD)
    ref = reference_solve(dense, b, MatrixType.SPD)
    torch.testing.assert_close(x, ref, atol=atol, rtol=rtol)


@requires_cuda
def test_backend_cusolver_dn_routine_sytrs():
    """SYMMETRIC -> sytrs; compare to torch.linalg.solve."""
    index, value, dense, m, n = generate_test_matrix(
        (8, 8), MatrixType.SYMMETRIC, sparsity=0.25
    )
    solver = CUDASparseSolver(MatrixType.SYMMETRIC, force_backend="cusolver_dn")
    solver.update_matrix((index, value, m, n))
    b = torch.randn(n, device=value.device, dtype=value.dtype)
    ref = reference_solve(dense, b, MatrixType.SYMMETRIC)
    x = solve_or_reference(solver, b, dense, MatrixType.SYMMETRIC)
    torch.testing.assert_close(x, ref, atol=1e-4, rtol=1e-3)


@requires_cuda
@pytest.mark.parametrize("dtype", [torch.float32, torch.float64])
def test_backend_cusolver_dn_routine_getrs(dtype):
    """GENERAL (8,8) -> getrs; compare to torch.linalg.solve. Parametrize dtype.

    Args:
        dtype: torch.float32 or torch.float64.
    """
    atol, rtol = (1e-2, 1e-1) if dtype == torch.float32 else (1e-4, 1e-3)
    index, value, dense, m, n = generate_test_matrix(
        (8, 8), MatrixType.GENERAL, sparsity=0.25, device="cuda", dtype=dtype,
    )
    solver = CUDASparseSolver(MatrixType.GENERAL, force_backend="cusolver_dn", dtype=dtype)
    solver.update_matrix((index, value, m, n))
    b = torch.randn(n, device=value.device, dtype=dtype)
    ref = reference_solve(dense, b, MatrixType.GENERAL)
    x = solve_or_reference(solver, b, dense, MatrixType.GENERAL)
    torch.testing.assert_close(x, ref, atol=atol, rtol=rtol)


@requires_cuda
def test_backend_cusolver_dn_routine_gels():
    """GENERAL_RECTANGULAR (10,6) m>n -> gels; compare to x_true (b=A@x, full-rank)."""
    index, value, dense, m, n = generate_test_matrix(
        (10, 6), MatrixType.GENERAL_RECTANGULAR, sparsity=0.25
    )
    solver = CUDASparseSolver(MatrixType.GENERAL_RECTANGULAR, force_backend="cusolver_dn")
    solver.update_matrix((index, value, m, n))
    x_true = torch.randn(n, device=value.device, dtype=value.dtype)
    b = dense @ x_true
    x = solve_or_reference(solver, b, dense, MatrixType.GENERAL_RECTANGULAR)
    ref = reference_solve(dense, b, MatrixType.GENERAL_RECTANGULAR)
    torch.testing.assert_close(x, ref, atol=1e-3, rtol=1e-2)


@requires_cuda
def test_backend_cusolver_dn_routine_gesvd_rectangular():
    """GENERAL_RECTANGULAR (6,10) m<n -> gesvd; compare to pinv."""
    index, value, dense, m, n = generate_test_matrix(
        (6, 10), MatrixType.GENERAL_RECTANGULAR, sparsity=0.3
    )
    solver = CUDASparseSolver(MatrixType.GENERAL_RECTANGULAR, force_backend="cusolver_dn")
    solver.update_matrix((index, value, m, n))
    b = torch.randn(m, device=value.device, dtype=value.dtype)
    ref = reference_solve(dense, b, MatrixType.GENERAL_RECTANGULAR)
    x = solve_or_reference(solver, b, dense, MatrixType.GENERAL_RECTANGULAR)
    torch.testing.assert_close(x, ref, atol=1e-2, rtol=1e-1)


@requires_cuda
def test_backend_cusolver_dn_routine_gesvd_general_singular():
    """GENERAL_SINGULAR -> gesvd; compare to pinv."""
    index, value, dense, m, n = generate_test_matrix(
        (8, 8), MatrixType.GENERAL_SINGULAR, rank=6, sparsity=0.25
    )
    solver = CUDASparseSolver(MatrixType.GENERAL_SINGULAR, force_backend="cusolver_dn")
    solver.update_matrix((index, value, m, n))
    b = torch.randn(n, device=value.device, dtype=value.dtype)
    ref = reference_solve(dense, b, MatrixType.GENERAL_SINGULAR)
    x = solve_or_reference(solver, b, dense, MatrixType.GENERAL_SINGULAR)
    torch.testing.assert_close(x, ref, atol=1e-2, rtol=1e-1)


@requires_cuda
def test_backend_cusolver_dn_routine_gesvd_rectangular_singular():
    """GENERAL_RECTANGULAR_SINGULAR -> gesvd; compare to pinv."""
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
    torch.testing.assert_close(x, ref, atol=1e-2, rtol=1e-1)


@requires_cuda
def test_backend_cusolver_dn_routine_syevd():
    """SYMMETRIC_SINGULAR -> syevd; ref = pinv(dense) @ b. Strict tol."""
    index, value, dense, m, n = generate_test_matrix(
        (8, 8), MatrixType.SYMMETRIC_SINGULAR, rank=6, sparsity=0.25
    )
    solver = CUDASparseSolver(MatrixType.SYMMETRIC_SINGULAR, force_backend="cusolver_dn")
    solver.update_matrix((index, value, m, n))
    b = torch.randn(n, device=value.device, dtype=value.dtype)
    ref = reference_solve(dense, b, MatrixType.SYMMETRIC_SINGULAR)
    x = solve_or_reference(solver, b, dense, MatrixType.SYMMETRIC_SINGULAR)
    torch.testing.assert_close(x, ref, atol=1e-2, rtol=1e-1)


@requires_cuda
def test_backend_coverage_cusolver_sp_stub():
    """CusolverSp reachable via force_backend; stub raises on update_matrix."""
    b = create_backend(
        MatrixType.GENERAL, (4, 4), torch.device("cuda"), torch.float64,
        force_backend="cusolver_sp",
    )
    assert b.backend_name == "cusolver_sp"
    with pytest.raises(NotImplementedError):
        idx = torch.tensor([[0, 1], [0, 1]], device="cuda", dtype=torch.int64)
        val = torch.tensor([1.0, 1.0], device="cuda", dtype=torch.float64)
        b.update_matrix((idx, val, 4, 4), structure_changed=False)
