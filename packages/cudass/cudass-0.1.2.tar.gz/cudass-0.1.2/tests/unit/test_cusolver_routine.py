"""Unit tests for select_cusolver_routine (cusolver_dn_backend)."""

import pytest

from cudass.backends.cusolver_dn_backend import select_cusolver_routine
from cudass.types import MatrixType

pytest.importorskip("torch")


def test_select_cusolver_routine_spd():
    assert select_cusolver_routine(MatrixType.SPD, (8, 8)) == "potrs"


def test_select_cusolver_routine_symmetric():
    assert select_cusolver_routine(MatrixType.SYMMETRIC, (8, 8)) == "sytrs"


def test_select_cusolver_routine_symmetric_singular():
    assert select_cusolver_routine(MatrixType.SYMMETRIC_SINGULAR, (8, 8)) == "syevd"


def test_select_cusolver_routine_general_singular():
    assert select_cusolver_routine(MatrixType.GENERAL_SINGULAR, (8, 8)) == "gesvd"


def test_select_cusolver_routine_general_rectangular_singular():
    assert select_cusolver_routine(MatrixType.GENERAL_RECTANGULAR_SINGULAR, (8, 12)) == "gesvd"


def test_select_cusolver_routine_general_rectangular_overdetermined():
    """GENERAL_RECTANGULAR (10,6) m>n -> gels."""
    assert select_cusolver_routine(MatrixType.GENERAL_RECTANGULAR, (10, 6)) == "gels"


def test_select_cusolver_routine_general_rectangular_underdetermined():
    """GENERAL_RECTANGULAR (6,10) m<n -> gesvd."""
    assert select_cusolver_routine(MatrixType.GENERAL_RECTANGULAR, (6, 10)) == "gesvd"


def test_select_cusolver_routine_general():
    """GENERAL (8,8) -> getrs."""
    assert select_cusolver_routine(MatrixType.GENERAL, (8, 8)) == "getrs"
