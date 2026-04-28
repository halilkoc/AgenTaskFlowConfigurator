from __future__ import annotations
from app.infrastructure.persistence.file_correction_store import FileCorrectionStore
class ClearSelectorCorrectionsUseCase:
    def __init__(self, correction_store: FileCorrectionStore) -> None:
        self._correction_store = correction_store
    def execute(self) -> None:
        self._correction_store.clear()