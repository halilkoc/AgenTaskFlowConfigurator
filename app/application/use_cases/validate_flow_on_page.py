from __future__ import annotations
from app.domain.ports.browser_port import BrowserPort
from app.infrastructure.browser.flow_validator import FlowValidator
class ValidateFlowOnPageUseCase:
    def __init__(self, browser_port: BrowserPort) -> None:
        self._validator = FlowValidator(browser_port)
    async def execute(self, flow_config_json: str) -> str:
        return await self._validator.validate(flow_config_json)