"""Backend selection: select_backend and create_backend."""

from typing import Optional, Tuple

import torch

from cudass.backends.base import BackendBase
from cudass.backends.cudss_backend import CUDSSBackend
from cudass.types import MatrixType


def select_backend(
    matrix_type: MatrixType,
    shape: Tuple[int, int],
    prefer_dense: bool = False,
) -> str:
    """Choose backend name from matrix type and shape.

    Args:
        matrix_type: MatrixType (GENERAL, SYMMETRIC, SPD, GENERAL_RECTANGULAR, etc.).
        shape: (m, n) matrix dimensions.
        prefer_dense: If True, prefer cusolver_dn over cudss when applicable.

    Returns:
        "cudss", "cusolver_dn", or "cusolver_sp".
    """
    m, n = shape
    if prefer_dense:
        return "cusolver_dn"
    if matrix_type in (MatrixType.GENERAL_SINGULAR, MatrixType.SYMMETRIC_SINGULAR):
        return "cusolver_dn"
    if matrix_type == MatrixType.GENERAL_RECTANGULAR_SINGULAR:
        return "cusolver_dn"
    if matrix_type in (MatrixType.GENERAL, MatrixType.SYMMETRIC, MatrixType.SPD):
        return "cudss"
    if matrix_type == MatrixType.GENERAL_RECTANGULAR:
        # For rectangular A (m!=n), cuDSS has an RHS-shape assumption; use
        # prefer_dense=True or cusolver_dn until fixed.
        return "cudss"  # try first; caller retries on NOT_SUPPORTED
    return "cusolver_dn"


def create_backend(
    matrix_type: MatrixType,
    shape: Tuple[int, int],
    device: torch.device,
    dtype: torch.dtype,
    use_cache: bool = True,
    cache: Optional[object] = None,
    prefer_dense: bool = False,
    force_backend: Optional[str] = None,
) -> BackendBase:
    """Instantiate the backend for the given matrix type and shape.

    Args:
        matrix_type: MatrixType for the linear system.
        shape: (m, n) matrix dimensions.
        device: CUDA device for tensors.
        dtype: torch.float32 or torch.float64.
        use_cache: Whether to cache factorizations.
        cache: FactorizationCache instance (or None).
        prefer_dense: If True, select cusolver_dn when otherwise cudss would be chosen.
        force_backend: If set to 'cudss', 'cusolver_dn', or 'cusolver_sp', use that
            backend and do not fallback (e.g. cudss bindings missing will raise).

    Returns:
        BackendBase: cudss, cusolver_dn, or cusolver_sp backend instance.

    Raises:
        ValueError: When force_backend or selected backend name is not in
            'cudss', 'cusolver_dn', 'cusolver_sp'.
        RuntimeError: When force_backend is 'cudss' and cudss_bindings are
            not available (no fallback if force_backend is set).
    """
    if force_backend is not None:
        name = force_backend
        do_fallback = False
    else:
        name = select_backend(matrix_type, shape, prefer_dense=prefer_dense)
        do_fallback = True

    if name == "cudss":
        try:
            return CUDSSBackend(
                matrix_type=matrix_type,
                device=device,
                dtype=dtype,
                use_cache=use_cache,
                cache=cache,
            )
        except RuntimeError as e:
            if do_fallback and "cudss_bindings not available" in str(e):
                name = "cusolver_dn"
            else:
                raise
    if name == "cusolver_dn":
        from cudass.backends.cusolver_dn_backend import CusolverDnBackend

        return CusolverDnBackend(
            matrix_type=matrix_type,
            device=device,
            dtype=dtype,
            use_cache=use_cache,
            cache=cache,
        )
    if name == "cusolver_sp":
        from cudass.backends.cusolver_sp_backend import CusolverSpBackend

        return CusolverSpBackend(
            matrix_type=matrix_type,
            device=device,
            dtype=dtype,
            use_cache=use_cache,
            cache=cache,
        )
    raise ValueError(f"Unknown backend: {name}")
