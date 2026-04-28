from __future__ import annotations
import json
from pathlib import Path
from datetime import datetime
class SaveFlowConfigToFileUseCase:
    def __init__(self, base_dir: str = "saved_flows") -> None:
        self._base_dir = Path(base_dir)
        self._base_dir.mkdir(parents=True, exist_ok=True)
    def execute(self, flow_config_json: str, file_name: str = "") -> str:
        parsed = json.loads(flow_config_json)
        if not file_name.strip():
            flow_name = "flow_config"
            flow_items = parsed.get("flow_config", [])
            if flow_items:
                flow_name = flow_items[0].get("flow_name", "flow_config") or "flow_config"
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_name = f"{flow_name}_{timestamp}.json"
        if not file_name.lower().endswith(".json"):
            file_name += ".json"
        safe_file_name = file_name.replace(" ", "_")
        file_path = self._base_dir / safe_file_name
        file_path.write_text(
            json.dumps(parsed, ensure_ascii=False, indent=4),
            encoding="utf-8",
        )
        return str(file_path)