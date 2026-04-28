from __future__ import annotations
from app.domain.models.browser_session import BrowserSessionState
from app.domain.ports.browser_port import BrowserPort
class StartBrowserSessionUseCase:
    def __init__(self, browser_port: BrowserPort) -> None:
        self._browser_port = browser_port
    async def execute(
        self,
        target_url: str,
        browser_type: str = "chromium",
        headless: bool = False,
    ) -> BrowserSessionState:
        return await self._browser_port.start_session(
            target_url=target_url,
            browser_type=browser_type,
            headless=headless,
        )