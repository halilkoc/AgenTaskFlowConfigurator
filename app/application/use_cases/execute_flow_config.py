from __future__ import annotations
from app.domain.ports.browser_port import BrowserPort
from app.infrastructure.browser.flow_executor import FlowExecutor
class ExecuteFlowConfigUseCase:
    def __init__(self, browser_port: BrowserPort) -> None:
        self._executor = FlowExecutor(browser_port)
    async def execute(self, flow_config_json: str) -> str:
        return await self._executor.execute(flow_config_json)