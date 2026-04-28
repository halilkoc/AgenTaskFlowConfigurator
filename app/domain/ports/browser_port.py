from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Optional
from playwright.async_api import Page
from app.domain.models.browser_session import BrowserSessionState
class BrowserPort(ABC):
    @abstractmethod
    async def start_session(
        self,
        target_url: str,
        browser_type: str = "chromium",
        headless: bool = False,
    ) -> BrowserSessionState:
        raise NotImplementedError
    @abstractmethod
    async def stop_session(self) -> BrowserSessionState:
        raise NotImplementedError
    @abstractmethod
    async def get_session_state(self) -> BrowserSessionState:
        raise NotImplementedError
    @abstractmethod
    async def get_page(self) -> Optional[Page]:
        raise NotImplementedError