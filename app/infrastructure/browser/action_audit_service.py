from __future__ import annotations
from datetime import datetime
from pathlib import Path
class ActionAuditService:
    def __init__(self, screenshot_dir: str = "runtime_artifacts/screenshots") -> None:
        self._screenshot_dir = Path(screenshot_dir)
        self._screenshot_dir.mkdir(parents=True, exist_ok=True)
    def now_iso(self) -> str:
        return datetime.now().isoformat(timespec="seconds")
    def build_screenshot_path(
        self,
        category_key: str,
        action_index: int,
        action_type: str,
    ) -> str:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        safe_category = (category_key or "category").replace(" ", "_")
        safe_action_type = (action_type or "action").replace(" ", "_")
        file_name = f"{safe_category}_{action_index}_{safe_action_type}_{timestamp}.png"
        return str(self._screenshot_dir / file_name)