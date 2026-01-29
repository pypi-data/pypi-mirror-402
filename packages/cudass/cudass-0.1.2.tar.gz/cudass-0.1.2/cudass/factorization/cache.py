"""Factorization cache: get/put/clear, LRU, device-aware, thread-safe."""

import threading
from collections import OrderedDict
from typing import Any, Optional

import torch


class FactorizationCache:
    """Cache for solver factorizations. Device-aware, LRU eviction, thread-safe."""

    def __init__(self, max_size: int = 100):
        self.max_size = max_size
        self._cache: dict = {}  # device -> OrderedDict key -> (value,)
        self._lock = threading.Lock()

    def _device_key(self, device: torch.device) -> str:
        return str(device)

    def get(self, cache_key: str, device: torch.device) -> Optional[Any]:
        with self._lock:
            dk = self._device_key(device)
            if dk not in self._cache:
                return None
            od = self._cache[dk]
            if cache_key not in od:
                return None
            val = od.pop(cache_key)
            od[cache_key] = val
            return val

    def put(self, cache_key: str, factorization: Any, device: torch.device) -> None:
        with self._lock:
            dk = self._device_key(device)
            if dk not in self._cache:
                self._cache[dk] = OrderedDict()
            od = self._cache[dk]
            if cache_key in od:
                od.pop(cache_key)
            od[cache_key] = factorization
            while len(od) > self.max_size:
                od.popitem(last=False)

    def clear(self, device: Optional[torch.device] = None) -> None:
        with self._lock:
            if device is None:
                self._cache.clear()
            else:
                dk = self._device_key(device)
                if dk in self._cache:
                    del self._cache[dk]
