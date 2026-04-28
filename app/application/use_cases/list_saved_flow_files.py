from __future__ import annotations
from pathlib import Path
from typing import List, Dict, Any
class ListSavedFlowFilesUseCase:
    def __init__(self, base_dir: str = "saved_flows") -> None:
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)
    def execute(self) -> List[Dict[str, Any]]:
        results: List[Dict[str, Any]] = []
        for file_path in sorted(self._base_dir.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
            results.append(
                {
                    "file_name": file_path.name,
                    "file_path": str(file_path),
                }
            )
        return results