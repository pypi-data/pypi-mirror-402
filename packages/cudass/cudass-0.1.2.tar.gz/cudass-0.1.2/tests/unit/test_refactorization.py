"""Unit tests for RefactorizationManager.should_refactorize."""

import pytest
import torch

from cudass.factorization.refactorization import RefactorizationManager

pytest.importorskip("torch")


@pytest.fixture
def device():
    """CUDA if available, else CPU (RefactorizationManager is device-agnostic).

    Returns:
        torch.device: cuda or cpu.
    """
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def test_should_refactorize_old_none(device):
    """old_A is None -> (True, True).

    Args:
        device: torch.device for tensors.
    """
    mgr = RefactorizationManager()
    idx = torch.tensor([[0, 1], [0, 1]], device=device, dtype=torch.int64)
    val = torch.tensor([1.0, 2.0], device=device, dtype=torch.float64)
    new_A = (idx, val, 2, 2)
    needs, structure_changed = mgr.should_refactorize(None, new_A)
    assert needs is True
    assert structure_changed is True


def test_should_refactorize_same_structure_and_values(device):
    """Same (m,n), same indices, same values -> (False, False).

    Args:
        device: torch.device for tensors.
    """
    mgr = RefactorizationManager()
    idx = torch.tensor([[0, 1], [0, 1]], device=device, dtype=torch.int64)
    val = torch.tensor([1.0, 2.0], device=device, dtype=torch.float64)
    A = (idx, val, 2, 2)
    needs, structure_changed = mgr.should_refactorize(A, A)
    assert needs is False
    assert structure_changed is False


def test_should_refactorize_same_structure_different_values(device):
    """Same (m,n), same indices, different values -> (True, False).

    Args:
        device: torch.device for tensors.
    """
    mgr = RefactorizationManager()
    idx = torch.tensor([[0, 1], [0, 1]], device=device, dtype=torch.int64)
    val1 = torch.tensor([1.0, 2.0], device=device, dtype=torch.float64)
    val2 = torch.tensor([1.5, 2.5], device=device, dtype=torch.float64)
    old_A = (idx, val1, 2, 2)
    new_A = (idx, val2, 2, 2)
    needs, structure_changed = mgr.should_refactorize(old_A, new_A)
    assert needs is True
    assert structure_changed is False


def test_should_refactorize_shape_changed(device):
    """(m,n) changed -> (True, True).

    Args:
        device: torch.device for tensors.
    """
    mgr = RefactorizationManager()
    idx2 = torch.tensor([[0, 1], [0, 1]], device=device, dtype=torch.int64)
    idx3 = torch.tensor([[0, 1, 2], [0, 1, 2]], device=device, dtype=torch.int64)
    val2 = torch.tensor([1.0, 2.0], device=device, dtype=torch.float64)
    val3 = torch.tensor([1.0, 2.0, 3.0], device=device, dtype=torch.float64)
    old_A = (idx2, val2, 2, 2)
    new_A = (idx3, val3, 3, 3)
    needs, structure_changed = mgr.should_refactorize(old_A, new_A)
    assert needs is True
    assert structure_changed is True


def test_should_refactorize_indices_different_shape(device):
    """Same (m,n), indices different shape -> (True, True).

    Args:
        device: torch.device for tensors.
    """
    mgr = RefactorizationManager()
    idx1 = torch.tensor([[0, 1], [0, 1]], device=device, dtype=torch.int64)
    idx2 = torch.tensor([[0, 1, 1], [0, 1, 0]], device=device, dtype=torch.int64)
    val1 = torch.tensor([1.0, 2.0], device=device, dtype=torch.float64)
    val2 = torch.tensor([1.0, 2.0, 0.5], device=device, dtype=torch.float64)
    old_A = (idx1, val1, 2, 2)
    new_A = (idx2, val2, 2, 2)
    needs, structure_changed = mgr.should_refactorize(old_A, new_A)
    assert needs is True
    assert structure_changed is True


def test_should_refactorize_indices_different_content(device):
    """Same (m,n), indices same shape but different content -> (True, True).

    Args:
        device: torch.device for tensors.
    """
    mgr = RefactorizationManager()
    idx1 = torch.tensor([[0, 1], [0, 1]], device=device, dtype=torch.int64)
    idx2 = torch.tensor([[0, 1], [1, 0]], device=device, dtype=torch.int64)
    val = torch.tensor([1.0, 2.0], device=device, dtype=torch.float64)
    old_A = (idx1, val, 2, 2)
    new_A = (idx2, val, 2, 2)
    needs, structure_changed = mgr.should_refactorize(old_A, new_A)
    assert needs is True
    assert structure_changed is True
