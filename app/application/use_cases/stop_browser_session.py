from __future__ import annotations
from app.domain.models.browser_session import BrowserSessionState
from app.domain.ports.browser_port import BrowserPort
class StopBrowserSessionUseCase:
    def __init__(self, browser_port: BrowserPort) -> None:
        self._browser_port = browser_port
    async def execute(self) -> BrowserSessionState:
        return await self._browser_port.stop_session()