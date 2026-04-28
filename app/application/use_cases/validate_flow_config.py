from __future__ import annotations
import json
class ValidateFlowConfigUseCase:
    def execute(self, flow_config_json: str) -> str:
        if not flow_config_json.strip():
            raise ValueError("Flow config boş olamaz.")
        try:
            parsed = json.loads(flow_config_json)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Flow config geçerli JSON değil: {exc}") from exc
        if "flow_config" not in parsed:
            raise ValueError("Flow config içinde 'flow_config' alanı bulunamadı.")
        return json.dumps(parsed, ensure_ascii=False, indent=4)