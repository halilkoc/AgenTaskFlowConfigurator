from __future__ import annotations
from pathlib import Path
class LoadFlowConfigFromFileUseCase:
    def __init__(self, base_dir: str = "saved_flows") -> None:
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)
    def execute(self, file_name: str) -> str:
        if not file_name.strip():
            raise ValueError("Yüklenecek dosya adı boş olamaz.")
        file_path = self._base_dir / file_name
        if not file_path.exists():
            raise ValueError(f"Dosya bulunamadı: {file_name}")
        return file_path.read_text(encoding="utf-8")