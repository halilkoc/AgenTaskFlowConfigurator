from __future__ import annotations
import json
from copy import deepcopy
from typing import Any, Dict
class MergeFlowConfigsUseCase:
    def execute(
        self,
        existing_flow_config_json: str,
        new_flow_config_json: str,
    ) -> str:
        existing_parsed = self._safe_parse(existing_flow_config_json)
        new_parsed = self._safe_parse(new_flow_config_json)
        existing_items = existing_parsed.get("flow_config", [])
        new_items = new_parsed.get("flow_config", [])
        if not existing_items:
            return json.dumps(new_parsed, ensure_ascii=False, indent=4)
        if not new_items:
            return json.dumps(existing_parsed, ensure_ascii=False, indent=4)
        base_item = deepcopy(existing_items[0])
        incoming_item = deepcopy(new_items[0])
        base_categories: Dict[str, Any] = base_item.get("categories", {})
        incoming_categories: Dict[str, Any] = incoming_item.get("categories", {})
        base_execution_order = list(base_item.get("execution_order", []))
        incoming_execution_order = list(incoming_item.get("execution_order", []))
        key_mapping: Dict[str, str] = {}
        for incoming_key, incoming_category in incoming_categories.items():
            final_key = self._generate_unique_key(incoming_key, base_categories)
            key_mapping[incoming_key] = final_key
            base_categories[final_key] = incoming_category
        for incoming_key in incoming_execution_order:
            mapped_key = key_mapping.get(incoming_key, incoming_key)
            if mapped_key not in base_execution_order:
                base_execution_order.append(mapped_key)
        if not base_item.get("flow_name"):
            base_item["flow_name"] = incoming_item.get("flow_name", "Yeni_Akis")
        base_item["categories"] = base_categories
        base_item["execution_order"] = base_execution_order
        # parameters tarafında mevcut değerleri koru, eksikse yeniden doldur
        merged_parameters = deepcopy(existing_parsed.get("parameters", {}))
        incoming_parameters = new_parsed.get("parameters", {})
        for key, value in incoming_parameters.items():
            if key not in merged_parameters or self._is_empty_value(merged_parameters.get(key)):
                merged_parameters[key] = value
        merged_root = {
            "flow_config": [base_item],
            "parameters": merged_parameters,
        }
        return json.dumps(merged_root, ensure_ascii=False, indent=4)
    def _safe_parse(self, raw_json: str) -> Dict[str, Any]:
        if not raw_json.strip():
            return {"flow_config": [], "parameters": {}}
        parsed = json.loads(raw_json)
        if not isinstance(parsed, dict):
            raise ValueError("Flow config JSON object formatında olmalı.")
        parsed.setdefault("flow_config", [])
        parsed.setdefault("parameters", {})
        return parsed
    def _generate_unique_key(self, preferred_key: str, existing_categories: Dict[str, Any]) -> str:
        if preferred_key not in existing_categories:
            return preferred_key
        index = 2
        while f"{preferred_key}_{index}" in existing_categories:
            index += 1
        return f"{preferred_key}_{index}"
    def _is_empty_value(self, value: Any) -> bool:
        if value is None:
            return True
        if isinstance(value, str) and not value.strip():
            return True
        if isinstance(value, list) and len(value) == 0:
            return True
        if isinstance(value, dict) and len(value) == 0:
            return True
        return False