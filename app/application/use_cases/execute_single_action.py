from __future__ import annotations
from app.domain.ports.browser_port import BrowserPort
from app.infrastructure.browser.single_action_executor import SingleActionExecutor
class ExecuteSingleActionUseCase:
    def __init__(self, browser_port: BrowserPort) -> None:
        self._executor = SingleActionExecutor(browser_port)
    async def execute(
        self,
        flow_config_json: str,
        category_key: str,
        action_index: int,
    ) -> str:
        return await self._executor.execute(
            flow_config_json=flow_config_json,
            category_key=category_key,
            action_index=action_index,
        )