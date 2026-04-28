from __future__ import annotations
import json
from app.infrastructure.persistence.file_correction_store import FileCorrectionStore
class ApplyCorrectionsToFlowUseCase:
    def __init__(self, correction_store: FileCorrectionStore) -> None:
        self._correction_store = correction_store
    def execute(self, flow_config_json: str) -> str:
        parsed = json.loads(flow_config_json)
        for flow_item in parsed.get("flow_config", []):
            categories = flow_item.get("categories", {})
            for _, category in categories.items():
                for action in category.get("actions", []):
                    action_type = action.get("type", "")
                    description = action.get("description", "")
                    cached = self._correction_store.get(
                        action_type=action_type,
                        description=description,
                    )
                    if not cached:
                        continue
                    if not (action.get("selector") or "").strip():
                        action["selector"] = cached.get("selector", "")
                        action["context_name"] = cached.get("context_name", "main")
                        action["status"] = "selector_reused"
        return json.dumps(parsed, ensure_ascii=False, indent=4)