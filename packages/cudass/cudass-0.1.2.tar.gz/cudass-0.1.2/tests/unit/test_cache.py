"""Unit tests for FactorizationCache: get/put/clear, LRU, device-aware, thread-safety."""

import threading

import pytest
import torch

from cudass.factorization.cache import FactorizationCache

pytest.importorskip("torch")


@pytest.fixture
def device():
    """CUDA if available, else CPU (FactorizationCache uses device as key only).

    Returns:
        torch.device: cuda or cpu.
    """
    return torch.device("cuda" if torch.cuda.is_available() else "cpu")


def test_cache_get_empty(device):
    """get on empty -> None.

    Args:
        device: torch.device for cache key.
    """
    c = FactorizationCache(max_size=2)
    assert c.get("k1", device) is None


def test_cache_put_then_get(device):
    """put then get (same key, device) -> returns value.

    Args:
        device: torch.device for cache key.
    """
    c = FactorizationCache(max_size=2)
    c.put("k1", "v1", device)
    assert c.get("k1", device) == "v1"


def test_cache_get_different_key(device):
    """get on different key -> None.

    Args:
        device: torch.device for cache key.
    """
    c = FactorizationCache(max_size=2)
    c.put("k1", "v1", device)
    assert c.get("k2", device) is None


def test_cache_lru_eviction(device):
    """put 3 entries with max_size=2, then get oldest key -> None (LRU eviction).

    Args:
        device: torch.device for cache key.
    """
    c = FactorizationCache(max_size=2)
    c.put("k1", "v1", device)
    c.put("k2", "v2", device)
    c.put("k3", "v3", device)
    assert c.get("k1", device) is None
    assert c.get("k2", device) == "v2"
    assert c.get("k3", device) == "v3"


def test_cache_clear_device(device):
    """clear(device) -> get returns None for that device; other device unaffected.

    Args:
        device: torch.device for cache key.
    """
    c = FactorizationCache(max_size=2)
    c.put("k1", "v1", device)
    c.clear(device)
    assert c.get("k1", device) is None

    if torch.cuda.device_count() >= 2:
        d2 = torch.device("cuda:1")
        c.put("k1", "v1", device)
        c.put("k2", "v2", d2)
        c.clear(device)
        assert c.get("k1", device) is None
        assert c.get("k2", d2) == "v2"


def test_cache_clear_none(device):
    """clear(None) -> all devices empty.

    Args:
        device: torch.device for cache key.
    """
    c = FactorizationCache(max_size=2)
    c.put("k1", "v1", device)
    c.clear(None)
    assert c.get("k1", device) is None


def test_cache_thread_safety(device):
    """Spawn threads doing put/get/clear; no crash; final state consistent.

    Args:
        device: torch.device for cache key.
    """
    c = FactorizationCache(max_size=20)
    results = []

    def worker(tid, n):
        dev = device
        for i in range(n):
            key = f"t{tid}_{i}"
            c.put(key, f"val_{key}", dev)
        for i in range(n):
            key = f"t{tid}_{i}"
            v = c.get(key, dev)
            results.append((key, v))

    threads = [threading.Thread(target=worker, args=(i, 5)) for i in range(3)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    for key, v in results:
        assert v is not None, f"get({key}) should return a value"
        assert v == f"val_{key}"
