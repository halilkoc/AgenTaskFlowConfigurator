from __future__ import annotations
import json
from typing import Any, Dict
from app.domain.ports.browser_port import BrowserPort
from app.infrastructure.browser.flow_executor import FlowExecutor
class SingleActionExecutor:
    def __init__(self, browser_port: BrowserPort) -> None:
        self._browser_port = browser_port
        self._flow_executor = FlowExecutor(browser_port)
    async def execute(
        self,
        flow_config_json: str,
        category_key: str,
        action_index: int,
    ) -> str:
        parsed = json.loads(flow_config_json)
        flow_items = parsed.get("flow_config", [])
        if not flow_items:
            raise ValueError("flow_config bulunamadı.")
        categories: Dict[str, Any] = flow_items[0].get("categories", {})
        if category_key not in categories:
            raise ValueError(f"Kategori bulunamadı: {category_key}")
        actions = categories[category_key].get("actions", [])
        if action_index < 0 or action_index >= len(actions):
            raise ValueError("Action index geçersiz.")
        action = actions[action_index]
        page = await self._browser_port.get_page()
        if page is None:
            raise ValueError("Aktif browser sayfası bulunamadı. Önce oturum başlatılmalı.")
        await self._flow_executor._execute_action(page, category_key, action_index, action)
        return json.dumps(parsed, ensure_ascii=False, indent=4)