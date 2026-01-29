"""Tests that require built native extensions: cudss_bindings and sparse_to_dense.

Run after `pip install -e .` with CUDA and (for cudss) cuDSS available.
"""

import pytest
import torch

from tests.conftest import requires_cuda


def _sparse_to_dense_available():
    try:
        from cudass.cuda.kernels import sparse_to_dense
        idx = torch.tensor([[0], [0]], device="cuda", dtype=torch.int64)
        val = torch.tensor([1.0], device="cuda", dtype=torch.float64)
        sparse_to_dense(idx, val, 1, 1)
        return sparse_to_dense
    except (ImportError, RuntimeError):
        return None


@requires_cuda
def test_sparse_to_dense_kernel_built_and_works():
    """sparse_to_dense kernel must be built; run a minimal COO->dense conversion.
    Skips when the extension was not built (e.g. CUDA_HOME/nvcc not at build time).
    """
    try:
        import cudass.cuda.kernels._sparse_to_dense  # noqa: F401
    except ImportError:
        pytest.skip("sparse_to_dense kernel not built (need CUDA_HOME and nvcc at build)")

    from cudass.cuda.kernels import sparse_to_dense

    index = torch.tensor([[0, 1], [0, 1]], device="cuda", dtype=torch.int64)
    value = torch.tensor([1.0, 2.0], device="cuda", dtype=torch.float64)
    out = sparse_to_dense(index, value, 2, 2)
    assert out.shape == (2, 2)
    assert out[0, 0].item() == 1.0 and out[1, 1].item() == 2.0
    assert out[0, 1].item() == 0.0 and out[1, 0].item() == 0.0


@requires_cuda
def test_sparse_to_dense_float32():
    """sparse_to_dense with float32: (index, value_f32, 2, 2) -> correct 2x2 dense."""
    s2d = _sparse_to_dense_available()
    if s2d is None:
        pytest.skip("sparse_to_dense kernel not built")
    index = torch.tensor([[0, 1], [0, 1]], device="cuda", dtype=torch.int64)
    value = torch.tensor([1.0, 2.0], device="cuda", dtype=torch.float32)
    out = s2d(index, value, 2, 2)
    assert out.shape == (2, 2)
    assert out.dtype == torch.float32
    assert out[0, 0].item() == pytest.approx(1.0) and out[1, 1].item() == pytest.approx(2.0)


@requires_cuda
def test_sparse_to_dense_empty_coo():
    """Empty COO: index=[2,0], value size 0, m,n=2,2 -> zeros(2,2)."""
    s2d = _sparse_to_dense_available()
    if s2d is None:
        pytest.skip("sparse_to_dense kernel not built")
    index = torch.empty(2, 0, device="cuda", dtype=torch.int64)
    value = torch.empty(0, device="cuda", dtype=torch.float64)
    out = s2d(index, value, 2, 2)
    assert out.shape == (2, 2)
    torch.testing.assert_close(out, torch.zeros(2, 2, device="cuda", dtype=torch.float64))


@requires_cuda
def test_sparse_to_dense_single_element():
    """Single element: (i,j)=(1,1), v=3.0 -> out[1,1]==3.0."""
    s2d = _sparse_to_dense_available()
    if s2d is None:
        pytest.skip("sparse_to_dense kernel not built")
    index = torch.tensor([[1], [1]], device="cuda", dtype=torch.int64)
    value = torch.tensor([3.0], device="cuda", dtype=torch.float64)
    out = s2d(index, value, 2, 2)
    assert out.shape == (2, 2)
    assert out[1, 1].item() == pytest.approx(3.0)
    assert out[0, 0].item() == 0.0 and out[0, 1].item() == 0.0 and out[1, 0].item() == 0.0


@requires_cuda
def test_cudss_bindings_built_and_works():
    """cudss_bindings must be built; create and destroy a handle."""
    import cudass.cuda.bindings.cudss_bindings as cudss

    h = cudss.create_handle()
    cudss.destroy_handle(h)
