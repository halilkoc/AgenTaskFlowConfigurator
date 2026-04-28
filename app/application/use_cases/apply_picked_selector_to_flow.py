from __future__ import annotations
import json
class ApplyPickedSelectorToFlowUseCase:
    def execute(
        self,
        flow_config_json: str,
        picked_selector: str,
        target_category_key: str,
        target_action_index: int,
    ) -> str:
        if not picked_selector.strip():
            raise ValueError("Uygulanacak picked selector boş.")
        parsed = json.loads(flow_config_json)
        flow_items = parsed.get("flow_config", [])
        if not flow_items:
            raise ValueError("flow_config bulunamadı.")
        categories = flow_items[0].get("categories", {})
        if target_category_key not in categories:
            raise ValueError(f"Kategori bulunamadı: {target_category_key}")
        actions = categories[target_category_key].get("actions", [])
        if target_action_index < 0 or target_action_index >= len(actions):
            raise ValueError("Action index geçersiz.")
        actions[target_action_index]["selector"] = picked_selector
        actions[target_action_index]["status"] = "selector_updated"
        return json.dumps(parsed, ensure_ascii=False, indent=4)