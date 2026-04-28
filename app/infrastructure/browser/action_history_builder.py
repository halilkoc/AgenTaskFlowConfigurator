from __future__ import annotations
import json
from typing import Any, Dict, List
class ActionHistoryBuilder:
    def build(self, flow_config_json: str) -> List[Dict[str, Any]]:
        parsed = json.loads(flow_config_json)
        results: List[Dict[str, Any]] = []
        for flow_item in parsed.get("flow_config", []):
            categories = flow_item.get("categories", {})
            for category_key, category in categories.items():
                for index, action in enumerate(category.get("actions", [])):
                    results.append(
                        {
                            "category_key": category_key,
                            "action_index": index,
                            "action_type": action.get("type", ""),
                            "description": action.get("description", ""),
                            "status": action.get("status", ""),
                            "last_run_at": action.get("last_run_at", ""),
                            "run_count": action.get("run_count", 0),
                            "execution_error": action.get("execution_error", ""),
                            "screenshot_path": action.get("screenshot_path", ""),
                        }
                    )
        return results