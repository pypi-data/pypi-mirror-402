"""import packages"""
import time
from typing import Dict, Any

class TTLCache:
    """Simple in-memory TTL cache."""

    def __init__(self, ttl_seconds: int):
        self.ttl = ttl_seconds
        self._store: Dict[str, Dict[str, Any]] = {}

    def get(self, key: str):
        entry = self._store.get(key)
        if not entry:
            return None
        if time.time() > entry["expires_at"]:
            self._store.pop(key, None)
            return None
        return entry["value"]

    def set(self, key: str, value: Any):
        self._store[key] = {
            "value": value,
            "expires_at": time.time() + self.ttl,
        }

    def clear(self):
        self._store.clear()
