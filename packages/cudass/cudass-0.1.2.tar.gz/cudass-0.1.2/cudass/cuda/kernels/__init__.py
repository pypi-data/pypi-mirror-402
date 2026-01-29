# cudass CUDA kernels
from typing import Optional

import torch

try:
    from cudass.cuda.kernels._sparse_to_dense import sparse_to_dense as _sparse_to_dense_impl
except ImportError:
    _sparse_to_dense_impl = None


def sparse_to_dense(
    index: torch.Tensor,
    value: torch.Tensor,
    m: int,
    n: int,
    out: Optional[torch.Tensor] = None,
) -> torch.Tensor:
    """COO (index [2,nnz], value [nnz]) to dense [m,n], on GPU.

    Args:
        index: COO indices [2, nnz], int64, CUDA.
        value: COO values [nnz], float32/float64, CUDA.
        m: Number of rows.
        n: Number of columns.
        out: Optional output tensor [m, n]; if None, allocated.

    Returns:
        Dense tensor [m, n], same dtype and device as value (or out).

    Raises:
        RuntimeError: If sparse_to_dense kernel is not built.
    """
    if _sparse_to_dense_impl is None:
        raise RuntimeError("sparse_to_dense kernel not built; install with CUDA and PyTorch")
    if out is None:
        out = torch.zeros(m, n, dtype=value.dtype, device=value.device)
    _sparse_to_dense_impl(index, value, out, m, n)
    return out
