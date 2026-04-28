from __future__ import annotations
from typing import Dict, Any
from app.infrastructure.persistence.file_correction_store import FileCorrectionStore
class ListSelectorCorrectionsUseCase:
    def __init__(self, correction_store: FileCorrectionStore) -> None:
        self._correction_store = correction_store
    def execute(self) -> Dict[str, Dict[str, Any]]:
        return self._correction_store.list_all()