from __future__ import annotations
import json
from typing import List, Dict, Any
class ListFlowActionsUseCase:
    def execute(self, flow_config_json: str) -> List[Dict[str, Any]]:
        if not flow_config_json.strip():
            return []
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
                            "selector": action.get("selector", ""),
                            "status": action.get("status", ""),
                            "label": f"{category_key} / #{index} / {action.get('type', '')} / {action.get('description', '')}",
                        }
                    )
        return results