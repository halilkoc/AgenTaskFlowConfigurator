from __future__ import annotations
import asyncio
from typing import Optional
from playwright.async_api import Browser, BrowserContext, Page, Playwright, async_playwright
from app.domain.models.browser_session import BrowserSessionState
from app.domain.ports.browser_port import BrowserPort
class PlaywrightBrowserRuntime(BrowserPort):
    def __init__(self) -> None:
        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._context: Optional[BrowserContext] = None
        self._page: Optional[Page] = None
        self._state = BrowserSessionState()
        self._lock = asyncio.Lock()
    async def start_session(
        self,
        target_url: str,
        browser_type: str = "chromium",
        headless: bool = False,
    ) -> BrowserSessionState:
        async with self._lock:
            try:
                if self._browser is not None:
                    await self._cleanup_locked()
                self._playwright = await async_playwright().start()
                if browser_type == "firefox":
                    self._browser = await self._playwright.firefox.launch(headless=headless)
                elif browser_type == "webkit":
                    self._browser = await self._playwright.webkit.launch(headless=headless)
                else:
                    self._browser = await self._playwright.chromium.launch(headless=headless)
                self._context = await self._browser.new_context()
                self._page = await self._context.new_page()
                navigated_url = ""
                normalized_url = (target_url or "").strip()
                if normalized_url:
                    if not normalized_url.startswith(("http://", "https://")):
                        normalized_url = f"https://{normalized_url}"
                    await self._page.goto(
                        normalized_url,
                        wait_until="domcontentloaded",
                        timeout=30000,
                    )
                    navigated_url = self._page.url
                self._state = BrowserSessionState(
                    is_running=True,
                    current_url=navigated_url,
                    browser_type=browser_type,
                    headless=headless,
                    status_message="Browser oturumu başarıyla başlatıldı.",
                    last_error="",
                )
                return self._state
            except Exception as exc:
                await self._cleanup_locked()
                self._state = BrowserSessionState(
                    is_running=False,
                    current_url="",
                    browser_type=browser_type,
                    headless=headless,
                    status_message="Browser oturumu başlatılamadı.",
                    last_error=str(exc),
                )
                return self._state
    async def stop_session(self) -> BrowserSessionState:
        async with self._lock:
            try:
                await self._cleanup_locked()
                self._state = BrowserSessionState(
                    is_running=False,
                    current_url="",
                    browser_type=self._state.browser_type,
                    headless=self._state.headless,
                    status_message="Browser oturumu sonlandırıldı.",
                    last_error="",
                )
                return self._state
            except Exception as exc:
                self._state = BrowserSessionState(
                    is_running=False,
                    current_url="",
                    browser_type=self._state.browser_type,
                    headless=self._state.headless,
                    status_message="Browser oturumu sonlandırılırken hata oluştu.",
                    last_error=str(exc),
                )
                return self._state
    async def get_session_state(self) -> BrowserSessionState:
        async with self._lock:
            if self._page is not None:
                self._state.current_url = self._page.url
            return self._state
    async def get_page(self) -> Optional[Page]:
        async with self._lock:
            return self._page
    async def _cleanup_locked(self) -> None:
        if self._page is not None:
            try:
                await self._page.close()
            except Exception:
                pass
            finally:
                self._page = None
        if self._context is not None:
            try:
                await self._context.close()
            except Exception:
                pass
            finally:
                self._context = None
        if self._browser is not None:
            try:
                await self._browser.close()
            except Exception:
                pass
            finally:
                self._browser = None
        if self._playwright is not None:
            try:
                await self._playwright.stop()
            except Exception:
                pass
            finally:
                self._playwright = None