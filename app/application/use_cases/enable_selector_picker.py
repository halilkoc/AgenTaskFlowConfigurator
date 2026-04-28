from __future__ import annotations
from app.domain.ports.browser_port import BrowserPort
from app.infrastructure.browser.selector_picker import SelectorPickerService
class EnableSelectorPickerUseCase:
    def __init__(self, browser_port: BrowserPort) -> None:
        self._browser_port = browser_port
        self._picker_service = SelectorPickerService()
    async def execute(self) -> None:
        page = await self._browser_port.get_page()
        if page is None:
            raise ValueError("Aktif browser sayfası bulunamadı.")
        await self._picker_service.enable_picker(page)