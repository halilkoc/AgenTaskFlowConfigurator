from __future__ import annotations
from app.infrastructure.persistence.in_memory_correction_store import InMemoryCorrectionStore
class SaveSelectorCorrectionUseCase:
    def __init__(self, correction_store: InMemoryCorrectionStore) -> None:
        self._correction_store = correction_store
    def execute(
        self,
        action_type: str,
        description: str,
        selector: str,
        context_name: str = "main",
    ) -> None:
        if not selector.strip():
            raise ValueError("Kaydedilecek selector boş olamaz.")
        self._correction_store.save(
            action_type=action_type,
            description=description,
            selector=selector,
            context_name=context_name,
        )