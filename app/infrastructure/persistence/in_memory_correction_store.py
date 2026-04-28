from __future__ import annotations
from threading import Lock
from typing import Dict, Any, Optional
class InMemoryCorrectionStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._items: Dict[str, Dict[str, Any]] = {}
    def _build_key(self, action_type: str, description: str) -> str:
        return f"{(action_type or '').strip().lower()}::{(description or '').strip().lower()}"
    def save(
        self,
        action_type: str,
        description: str,
        selector: str,
        context_name: str = "main",
    ) -> None:
        key = self._build_key(action_type, description)
        with self._lock:
            self._items[key] = {
                "selector": selector,
                "context_name": context_name,
            }
    def get(
        self,
        action_type: str,
        description: str,
    ) -> Optional[Dict[str, Any]]:
        key = self._build_key(action_type, description)
        with self._lock:
            value = self._items.get(key)
            return dict(value) if value else None