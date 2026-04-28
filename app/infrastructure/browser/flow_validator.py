from __future__ import annotations
import json
from typing import Any, Dict, List
from playwright.async_api import Frame, Page
from app.domain.ports.browser_port import BrowserPort
from app.infrastructure.browser.page_context_service import PageContextService
class FlowValidator:
    def __init__(self, browser_port: BrowserPort) -> None:
        self._browser_port = browser_port
        self._page_context_service = PageContextService()
    async def validate(self, flow_config_json: str) -> str:
        parsed = json.loads(flow_config_json)
        page = await self._browser_port.get_page()
        if page is None:
            raise ValueError("Aktif browser sayfası bulunamadı. Önce oturum başlatılmalı.")
        results: List[Dict[str, Any]] = []
        for flow_item in parsed.get("flow_config", []):
            categories = flow_item.get("categories", {})
            execution_order = flow_item.get("execution_order", [])
            category_keys = execution_order or list(categories.keys())
            for category_key in category_keys:
                category = categories.get(category_key)
                if not category:
                    continue
                actions = category.get("actions", [])
                for index, action in enumerate(actions):
                    result = await self._validate_action(page, category_key, index, action)
                    results.append(result)
        return json.dumps(results, ensure_ascii=False, indent=4)
    async def _get_context(self, page: Page, context_name: str) -> Page | Frame:
        contexts = await self._page_context_service.get_all_contexts(page)
        for name, context in contexts:
            if name == context_name:
                return context
        return page
    async def _validate_action(
        self,
        page: Page,
        category_key: str,
        action_index: int,
        action: Dict[str, Any],
    ) -> Dict[str, Any]:
        action_type = (action.get("type") or "").strip().lower()
        selector = (action.get("selector") or "").strip()
        context_name = (action.get("context_name") or "main").strip()
        description = action.get("description") or ""
        prompt = action.get("prompt") or ""
        base_result = {
            "category_key": category_key,
            "action_index": action_index,
            "action_type": action_type,
            "description": description,
            "prompt": prompt,
            "selector": selector,
            "context_name": context_name,
            "is_valid": False,
            "message": "",
        }
        if action_type == "navigate":
            url = (action.get("url") or "").strip()
            if url:
                base_result["is_valid"] = True
                base_result["message"] = "Navigate action için URL mevcut."
            else:
                base_result["message"] = "Navigate action için URL boş."
            return base_result
        if not selector:
            base_result["message"] = "Selector boş."
            return base_result
        try:
            context = await self._get_context(page, context_name)
            locator = context.locator(f"xpath={selector}")
            count = await locator.count()
            if count < 1:
                base_result["message"] = "Selector sayfada bulunamadı."
                return base_result
            is_visible = await locator.first.is_visible()
            if not is_visible:
                base_result["message"] = "Selector bulundu ama görünür değil."
                return base_result
            base_result["is_valid"] = True
            base_result["message"] = "Selector bulundu ve görünür."
            return base_result
        except Exception as exc:
            base_result["message"] = f"Validation hatası: {str(exc)}"
            return base_result