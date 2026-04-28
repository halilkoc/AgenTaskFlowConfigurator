from __future__ import annotations
import base64
import json
from typing import Any, Dict, List, Optional
import httpx
from app.domain.models.llm_models import LLMPlanResult, PlannedAction, PlannedCategory
from app.domain.ports.llm_port import LLMPort
from app.shared.config.settings import get_settings
class QwenLLMClient(LLMPort):
    def __init__(self) -> None:
        self._settings = get_settings()
    def generate_plan(
        self,
        user_prompt: str,
        selected_mode: str,
        target_url: str,
    ) -> LLMPlanResult:
        system_prompt = self._build_system_prompt()
        user_content = self._build_user_prompt(
            user_prompt=user_prompt,
            selected_mode=selected_mode,
            target_url=target_url,
        )
        payload = self._build_payload(
            system_prompt=system_prompt,
            user_prompt=user_content,
        )
        headers = self._build_headers()
        request_url = self._normalize_url(self._settings.llm_base_url)
        with httpx.Client(timeout=self._settings.llm_timeout, verify=False) as client:
            response = client.post(
                request_url,
                headers=headers,
                json=payload,
            )
        if response.status_code == 401:
            raise ValueError(
                f"LLM yetkilendirme hatası (401). URL={request_url} | "
                f"Response={response.text}"
            )
        response.raise_for_status()
        data = response.json()
        raw_text = self._extract_content_text(data)
        parsed_json = self._extract_json_block(raw_text)
        return self._parse_plan_result(parsed_json, raw_text)
    def _normalize_url(self, url: str) -> str:
        normalized = (url or "").strip()
        if not normalized:
            raise ValueError("LLM_BASE_URL boş olamaz.")
        if normalized.startswith("https://https://"):
            normalized = normalized.replace("https://https://", "https://", 1)
        elif normalized.startswith("http://http://"):
            normalized = normalized.replace("http://http://", "http://", 1)
        return normalized
    def _build_headers(self) -> Dict[str, str]:
        headers = {
            "Content-Type": "application/json",
        }
        auth_type = (self._settings.llm_auth_type or "").strip().lower()
        if auth_type == "basic":
            username = self._settings.llm_username.strip()
            password = self._settings.llm_password.strip()
            if not username or not password:
                raise ValueError(
                    "LLM basic auth için LLM_USERNAME ve LLM_PASSWORD dolu olmalı."
                )
            token = base64.b64encode(
                f"{username}:{password}".encode("utf-8")
            ).decode("utf-8")
            headers["Authorization"] = f"Basic {token}"
        elif auth_type == "bearer":
            api_key = self._settings.llm_api_key.strip()
            if not api_key:
                raise ValueError("LLM bearer auth için LLM_API_KEY dolu olmalı.")
            headers["Authorization"] = f"Bearer {api_key}"
        return headers
    def _build_payload(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        return {
            "model": self._settings.llm_model_name,
            "temperature": self._settings.llm_temperature,
            "messages": [
                {
                    "role": "system",
                    "content": system_prompt,
                },
                {
                    "role": "user",
                    "content": user_prompt,
                },
            ],
        }
    def _build_system_prompt(self) -> str:
        return """
Sen bir browser/masaustu otomasyon planlayicisisin.
Gorevin, kullanicinin verdigi prompt'u action plan'a donusturmektir.
Kurallar:
1. Sadece JSON don.
2. JSON disinda hicbir aciklama yazma.
3. JSON semasi su yapida olacak:
{
  "flow_name": "string",
  "categories": [
    {
      "category_key": "string",
      "category_id": "01",
      "category_name": "string",
      "description": "string",
      "actions": [
        {
          "action_type": "navigate|click|fill|type|focus_and_fill|select|wait",
          "target_description": "string",
          "value": "string|null",
          "url": "string|null",
          "prompt": "string",
          "timeout": 10000
        }
      ]
    }
  ],
  "execution_order": ["CategoryKey1", "CategoryKey2"]
}
4. Her action icin prompt alani mutlaka dolu olmali.
5. Selector uretme. Selector alanlarini bos birak, sadece hedef aciklamasi uret.
6. Eger browser modunda URL verilmis ise ilk uygun action navigate olabilir.
7. Kategori sayisini minimumda tut ama mantikli parcala.
8. flow_name alanini Turkce karakter icermeyecek sekilde okunur bir yapiyla uret.
9. JSON valid olmali.
        """.strip()
    def _build_user_prompt(
        self,
        user_prompt: str,
        selected_mode: str,
        target_url: str,
    ) -> str:
        return f"""
Calisma modu: {selected_mode}
Hedef URL: {target_url or "YOK"}
Kullanici promptu:
{user_prompt}
        """.strip()
    def _extract_content_text(self, response_json: Dict[str, Any]) -> str:
        choices: List[Dict[str, Any]] = response_json.get("choices", [])
        if not choices:
            raise ValueError(f"LLM response icinde choices alani bulunamadi: {response_json}")
        first_choice = choices[0]
        message = first_choice.get("message", {})
        content = message.get("content", "")
        if isinstance(content, list):
            parts: List[str] = []
            for item in content:
                if isinstance(item, dict) and item.get("type") == "text":
                    parts.append(item.get("text", ""))
                elif isinstance(item, str):
                    parts.append(item)
            return "\n".join(parts).strip()
        if isinstance(content, str):
            return content.strip()
        raise ValueError(f"LLM content alani beklenen formatta degil: {content}")
    def _extract_json_block(self, raw_text: str) -> Dict[str, Any]:
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.replace("```json", "").replace("```", "").strip()
        try:
            return json.loads(cleaned)
        except json.JSONDecodeError as exc:
            raise ValueError(f"LLM valid JSON donmedi. Ham cikti: {raw_text}") from exc
    def _safe_str(self, value: Any, default: str = "") -> str:
        if value is None:
            return default
        if isinstance(value, str):
            return value.strip()
        return str(value).strip()
    def _safe_int(self, value: Any, default: int = 10000) -> int:
        try:
            if value is None:
                return default
            return int(value)
        except (TypeError, ValueError):
            return default
    def _build_action_prompt(
        self,
        action_type: str,
        target_description: str,
        raw_prompt: Optional[Any],
    ) -> str:
        prompt_value = self._safe_str(raw_prompt, "")
        if prompt_value:
            return prompt_value
        if target_description:
            return f"{action_type} işlemini '{target_description}' hedefi için uygula."
        return f"{action_type} işlemini uygula."
    def _parse_plan_result(
        self,
        parsed_json: Dict[str, Any],
        raw_text: str,
    ) -> LLMPlanResult:
        categories: List[PlannedCategory] = []
        for category in parsed_json.get("categories", []):
            category_key = self._safe_str(category.get("category_key"), "Category_01")
            category_id = self._safe_str(category.get("category_id"), "01")
            category_name = self._safe_str(category.get("category_name"), category_key)
            category_description = self._safe_str(category.get("description"), category_name)
            actions: List[PlannedAction] = []
            for action in category.get("actions", []):
                action_type = self._safe_str(action.get("action_type"), "click")
                target_description = self._safe_str(
                    action.get("target_description"),
                    "Hedef açıklaması verilmedi",
                )
                action_prompt = self._build_action_prompt(
                    action_type=action_type,
                    target_description=target_description,
                    raw_prompt=action.get("prompt"),
                )
                actions.append(
                    PlannedAction(
                        action_type=action_type,
                        target_description=target_description,
                        value=self._safe_str(action.get("value"), "") or None,
                        url=self._safe_str(action.get("url"), "") or None,
                        prompt=action_prompt,
                        timeout=self._safe_int(action.get("timeout"), 10000),
                    )
                )
            categories.append(
                PlannedCategory(
                    category_key=category_key,
                    category_id=category_id,
                    category_name=category_name,
                    description=category_description,
                    actions=actions,
                )
            )
        return LLMPlanResult(
            flow_name=self._safe_str(parsed_json.get("flow_name"), "Yeni_Akis"),
            categories=categories,
            execution_order=[
                self._safe_str(item) for item in parsed_json.get("execution_order", [])
                if self._safe_str(item)
            ],
            raw_text=raw_text,
        )