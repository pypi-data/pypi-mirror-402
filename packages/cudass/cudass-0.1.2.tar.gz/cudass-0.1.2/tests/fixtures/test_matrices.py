"""Test fixtures: generate_test_matrix for each MatrixType."""

from typing import Optional, Tuple

import torch

from cudass.types import MatrixType


def generate_test_matrix(
    shape: Tuple[int, int],
    matrix_type: MatrixType,
    condition_number: float = 1e6,
    rank: Optional[int] = None,
    sparsity: float = 0.1,
    device: str = "cuda",
    dtype: torch.dtype = torch.float64,
) -> Tuple[torch.Tensor, torch.Tensor, torch.Tensor, int, int]:
    """Generate (index, value, dense_matrix, m, n) with known properties.

    Args:
        shape: (m, n) matrix shape.
        matrix_type: MatrixType enum.
        condition_number: Target condition number.
        rank: For singular types, effective rank.
        sparsity: Target sparsity.
        device: Device string (e.g. 'cuda').
        dtype: torch.float32 or torch.float64.

    Returns:
        Tuple of (index, value, dense, m, n).

    Raises:
        ValueError: If shape is inconsistent with matrix_type (e.g. square for rect).
    """
    m, n = shape
    if matrix_type in (MatrixType.GENERAL, MatrixType.GENERAL_SINGULAR, MatrixType.SYMMETRIC,
                       MatrixType.SYMMETRIC_SINGULAR, MatrixType.SPD):
        if m != n:
            raise ValueError(f"{matrix_type} requires square matrix")
    if matrix_type in (MatrixType.GENERAL_RECTANGULAR, MatrixType.GENERAL_RECTANGULAR_SINGULAR):
        if m == n:
            raise ValueError(f"{matrix_type} requires rectangular matrix")

    rng = torch.Generator(device=device).manual_seed(42)
    small = 1.0 / (condition_number ** 0.5) if condition_number > 1 else 1.0

    if matrix_type == MatrixType.SPD:
        # Build (index, value) so that dense = zeros; dense[ind]=val is SPD
        # (diagonally dominant symmetric with positive diagonal).
        nnz_target = max(m + 2, int(m * m * sparsity))
        diag_val = 2.0 + m * 0.2
        off_val_max = 0.12
        entries: dict = {}
        for i in range(m):
            entries[(i, i)] = float(diag_val)
        off_pairs = max(0, (nnz_target - m) // 2)
        for _ in range(off_pairs):
            i = int(torch.randint(m, (1,), device=device, generator=rng).item())
            j = int(torch.randint(m, (1,), device=device, generator=rng).item())
            if i == j or (i, j) in entries:
                continue
            u = torch.rand(1, device=device, dtype=dtype, generator=rng).item()
            v = (u * 2 - 1) * off_val_max
            entries[(i, j)] = float(v)
            entries[(j, i)] = float(v)
        rows = [k[0] for k in entries]
        cols = [k[1] for k in entries]
        vals = [entries[k] for k in entries]
        index = torch.tensor([rows, cols], device=device, dtype=torch.int64)
        value = torch.tensor(vals, device=device, dtype=dtype)
        dense = torch.zeros(m, m, device=device, dtype=dtype)
        dense[index[0], index[1]] = value
        return index, value, dense, m, m
    elif matrix_type == MatrixType.SYMMETRIC:
        A = torch.randn(m, m, device=device, dtype=dtype, generator=rng)
        A = (A + A.T) / 2 + torch.eye(m, device=device, dtype=dtype) * (1 + small)
    elif matrix_type == MatrixType.SYMMETRIC_SINGULAR:
        A = torch.randn(m, m, device=device, dtype=dtype, generator=rng)
        A = (A + A.T) / 2
        ev, V = torch.linalg.eigh(A)
        r = rank if rank is not None else max(1, m - 1)
        ev[r:] = 0
        A = V @ torch.diag(ev.clamp(min=small)) @ V.T
    elif matrix_type == MatrixType.GENERAL:
        A = torch.randn(m, m, device=device, dtype=dtype, generator=rng)
        A = A + torch.eye(m, device=device, dtype=dtype) * (1 + small)
    elif matrix_type == MatrixType.GENERAL_SINGULAR:
        A = torch.randn(m, m, device=device, dtype=dtype, generator=rng)
        U, _, Vh = torch.linalg.svd(A, full_matrices=True)
        s = torch.rand(m, device=device, dtype=dtype, generator=rng).clamp(min=small)
        r = rank if rank is not None else max(1, m - 1)
        s[r:] = 0
        A = U @ torch.diag(s) @ Vh
    elif matrix_type == MatrixType.GENERAL_RECTANGULAR:
        A = torch.randn(m, n, device=device, dtype=dtype, generator=rng)
        k = min(m, n)
        A[:k, :k] = A[:k, :k] + torch.eye(k, device=device, dtype=dtype) * (1 + small)
    elif matrix_type == MatrixType.GENERAL_RECTANGULAR_SINGULAR:
        A = torch.randn(m, n, device=device, dtype=dtype, generator=rng)
        r = rank if rank is not None else min(m, n) - 1
        r = max(1, r)
        U, s, Vh = torch.linalg.svd(A, full_matrices=True)
        k = min(m, n)
        s = s.clamp(min=small)
        s[r:] = 0
        A = (U[:, :k] @ torch.diag(s) @ Vh[:k, :]).to(dtype)
    else:
        raise ValueError(f"Unknown matrix_type {matrix_type}")

    nnz_target = max(1, int(m * n * sparsity))
    idx = torch.randperm(m * n, device=device, generator=rng)[:nnz_target]
    rows = (idx // n).long()
    cols = (idx % n).long()
    index = torch.stack([rows, cols], dim=0)
    value = A[rows, cols].clone()
    for i in range(min(m, n)):
        if not ((index[0] == i) & (index[1] == i)).any():
            idx_ii = torch.tensor([[i], [i]], device=device, dtype=torch.int64)
            index = torch.cat([index, idx_ii], dim=1)
            value = torch.cat([value, A[i, i].unsqueeze(0)])
    # For symmetric types, add (j,i) for each (i,j) so sparse represents symmetric matrix
    if matrix_type in (MatrixType.SPD, MatrixType.SYMMETRIC, MatrixType.SYMMETRIC_SINGULAR):
        entries = {}
        for i in range(index.shape[1]):
            r, c = index[0, i].item(), index[1, i].item()
            entries[(r, c)] = value[i].item()
            if r != c and (c, r) not in entries:
                entries[(c, r)] = entries[(r, c)]
        rows = [k[0] for k in entries]
        cols = [k[1] for k in entries]
        index = torch.tensor([rows, cols], device=device, dtype=torch.int64)
        value = torch.tensor([entries[k] for k in entries], device=device, dtype=dtype)

    dense = torch.zeros(m, n, device=device, dtype=dtype)
    dense[index[0], index[1]] = value
    return index, value, dense, m, n
