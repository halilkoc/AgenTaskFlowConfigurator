from __future__ import annotations
import json
from pathlib import Path
from threading import Lock
from typing import Dict, Any, Optional
class FileCorrectionStore:
    def __init__(self, file_path: str = "app/infrastructure/persistence/data/corrections.json") -> None:
        self._file_path = Path(file_path)
        self._lock = Lock()
        self._ensure_file()
    def _ensure_file(self) -> None:
        self._file_path.parent.mkdir(parents=True, exist_ok=True)
        if not self._file_path.exists():
            self._file_path.write_text("{}", encoding="utf-8")
    def _build_key(self, action_type: str, description: str) -> str:
        return f"{(action_type or '').strip().lower()}::{(description or '').strip().lower()}"
    def _read_all(self) -> Dict[str, Dict[str, Any]]:
        self._ensure_file()
        try:
            raw = self._file_path.read_text(encoding="utf-8").strip()
            if not raw:
                return {}
            parsed = json.loads(raw)
            return parsed if isinstance(parsed, dict) else {}
        except Exception:
            return {}
    def _write_all(self, data: Dict[str, Dict[str, Any]]) -> None:
        self._file_path.write_text(
            json.dumps(data, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )
    def save(
        self,
        action_type: str,
        description: str,
        selector: str,
        context_name: str = "main",
    ) -> None:
        if not selector.strip():
            return
        key = self._build_key(action_type, description)
        with self._lock:
            all_items = self._read_all()
            all_items[key] = {
                "selector": selector,
                "context_name": context_name,
            }
            self._write_all(all_items)
    def get(
        self,
        action_type: str,
        description: str,
    ) -> Optional[Dict[str, Any]]:
        key = self._build_key(action_type, description)
        with self._lock:
            all_items = self._read_all()
            value = all_items.get(key)
            return dict(value) if value else None
    def list_all(self) -> Dict[str, Dict[str, Any]]:
        with self._lock:
            return self._read_all()
    def clear(self) -> None:
        with self._lock:
            self._write_all({})