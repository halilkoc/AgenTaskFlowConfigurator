from __future__ import annotations
import json
from typing import Any, Dict
from playwright.async_api import Frame, Page
from app.domain.ports.browser_port import BrowserPort
from app.infrastructure.browser.action_audit_service import ActionAuditService
from app.infrastructure.browser.page_context_service import PageContextService
from app.infrastructure.browser.selector_finder import SelectorFinder
class FlowExecutor:
    def __init__(self, browser_port: BrowserPort) -> None:
        self._browser_port = browser_port
        self._selector_finder = SelectorFinder()
        self._page_context_service = PageContextService()
        self._audit_service = ActionAuditService()
    async def execute(self, flow_config_json: str) -> str:
        parsed = json.loads(flow_config_json)
        page = await self._browser_port.get_page()
        if page is None:
            raise ValueError("Aktif browser sayfası bulunamadı. Önce oturum başlatılmalı.")
        initial_url = page.url
        for flow_item in parsed.get("flow_config", []):
            categories: Dict[str, Any] = flow_item.get("categories", {})
            execution_order = flow_item.get("execution_order", [])
            category_keys = execution_order or list(categories.keys())
            for category_key in category_keys:
                category = categories.get(category_key)
                if not category:
                    continue
                actions = category.get("actions", [])
                for action_index, action in enumerate(actions):
                    await self._execute_action(page, category_key, action_index, action)
        final_url = page.url
        if parsed.get("flow_config"):
            parsed["flow_config"][0]["global_settings"]["last_known_url"] = final_url
            parsed["flow_config"][0]["global_settings"]["initial_url"] = initial_url
        return json.dumps(parsed, ensure_ascii=False, indent=4)
    async def _get_context(self, page: Page, context_name: str) -> Page | Frame:
        contexts = await self._page_context_service.get_all_contexts(page)
        for name, context in contexts:
            if name == context_name:
                return context
        return page
    async def _take_failure_screenshot(
        self,
        page: Page,
        category_key: str,
        action_index: int,
        action_type: str,
        action: Dict[str, Any],
    ) -> None:
        try:
            screenshot_path = self._audit_service.build_screenshot_path(
                category_key=category_key,
                action_index=action_index,
                action_type=action_type,
            )
            await page.screenshot(path=screenshot_path, full_page=True)
            action["screenshot_path"] = screenshot_path
        except Exception:
            action["screenshot_path"] = None
    def _mark_action_run(self, action: Dict[str, Any]) -> None:
        action["last_run_at"] = self._audit_service.now_iso()
        action["run_count"] = int(action.get("run_count") or 0) + 1
    def _resolve_action_value(self, action: Dict[str, Any]) -> Any:
        value = action.get("value")
        if value is not None:
            return value
        return action.get("text")
    async def _resolve_selector_and_context(
        self,
        page: Page,
        action: Dict[str, Any],
        action_type: str,
        description: str,
        prompt: str,
        value: Any,
    ) -> tuple[str, str]:
        selector = (action.get("selector") or "").strip()
        context_name = action.get("context_name", "main")
        if selector:
            return selector, context_name
        selector_result = await self._selector_finder.find_selector_for_action(
            page=page,
            action_type=action_type,
            description=description,
            prompt=prompt,
            value=None if value is None else str(value),
        )
        selector = selector_result.get("selector", "")
        context_name = selector_result.get("context_name", "main")
        action["selector"] = selector
        action["context_name"] = context_name
        return selector, context_name
    async def _mark_failed(
        self,
        page: Page,
        category_key: str,
        action_index: int,
        action_type: str,
        action: Dict[str, Any],
        error_message: str,
    ) -> None:
        action["status"] = "failed"
        action["execution_error"] = error_message
        await self._take_failure_screenshot(page, category_key, action_index, action_type, action)
    async def _mark_success(
        self,
        action: Dict[str, Any],
        selector: str = "",
    ) -> None:
        action["status"] = "executed"
        action["execution_error"] = None
        action["screenshot_path"] = None
        if selector:
            action["validation_selector"] = selector
    async def _execute_action(
        self,
        page: Page,
        category_key: str,
        action_index: int,
        action: Dict[str, Any],
    ) -> None:
        action_type = (action.get("type") or "").strip().lower()
        description = action.get("description") or ""
        prompt = action.get("prompt") or ""
        timeout = int(action.get("timeout") or 10000)
        url = action.get("url")
        value = self._resolve_action_value(action)
        self._mark_action_run(action)
        try:
            if action_type == "navigate":
                target_url = (url or "").strip()
                if not target_url:
                    await self._mark_failed(
                        page, category_key, action_index, action_type, action,
                        "Navigate action için url boş.",
                    )
                    return
                await page.goto(target_url, wait_until="domcontentloaded", timeout=timeout)
                await self._mark_success(action)
                action["validation_selector"] = ""
                return
            if action_type == "wait":
                selector, context_name = await self._resolve_selector_and_context(
                    page, action, action_type, description, prompt, value
                )
                # Selector yoksa sadece süre kadar bekle
                if not selector:
                    wait_ms = int(value) if value not in (None, "") else timeout
                    await page.wait_for_timeout(wait_ms)
                    await self._mark_success(action)
                    action["validation_selector"] = ""
                    return
                context = await self._get_context(page, context_name)
                locator = context.locator(f"xpath={selector}").first
                await locator.wait_for(state="visible", timeout=timeout)
                await self._mark_success(action, selector=selector)
                return
            selector, context_name = await self._resolve_selector_and_context(
                page, action, action_type, description, prompt, value
            )
            if not selector:
                await self._mark_failed(
                    page, category_key, action_index, action_type, action,
                    "Uygun selector bulunamadı.",
                )
                return
            context = await self._get_context(page, context_name)
            locator = context.locator(f"xpath={selector}").first
            if action_type == "fill":
                if value is None:
                    await self._mark_failed(
                        page, category_key, action_index, action_type, action,
                        "Fill action için değer bulunamadı.",
                    )
                    return
                await locator.wait_for(state="visible", timeout=timeout)
                await locator.fill(str(value), timeout=timeout)
                await self._mark_success(action, selector=selector)
                return
            if action_type in {"type", "focus_and_fill"}:
                if value is None:
                    await self._mark_failed(
                        page, category_key, action_index, action_type, action,
                        "Type/focus_and_fill action için değer bulunamadı.",
                    )
                    return
                await locator.wait_for(state="visible", timeout=timeout)
                await locator.click(timeout=timeout)
                await locator.fill("")
                await locator.type(str(value), timeout=timeout)
                await self._mark_success(action, selector=selector)
                return
            if action_type == "click":
                before_url = page.url
                await locator.wait_for(state="visible", timeout=timeout)
                await locator.click(timeout=timeout)
                await page.wait_for_timeout(1500)
                await self._mark_success(action, selector=selector)
                if page.url != before_url:
                    action["navigation_happened"] = True
                    action["navigated_url"] = page.url
                else:
                    action["navigation_happened"] = False
                return
            if action_type == "hover":
                await locator.wait_for(state="visible", timeout=timeout)
                await locator.hover(timeout=timeout)
                await page.wait_for_timeout(500)
                await self._mark_success(action, selector=selector)
                return
            if action_type == "press":
                key_to_press = str(value).strip() if value is not None else ""
                if not key_to_press:
                    await self._mark_failed(
                        page, category_key, action_index, action_type, action,
                        "Press action için tuş değeri bulunamadı.",
                    )
                    return
                await locator.wait_for(state="visible", timeout=timeout)
                await locator.click(timeout=timeout)
                await locator.press(key_to_press, timeout=timeout)
                await self._mark_success(action, selector=selector)
                return
            if action_type == "check":
                await locator.wait_for(state="visible", timeout=timeout)
                await locator.check(timeout=timeout)
                await self._mark_success(action, selector=selector)
                return
            if action_type == "uncheck":
                await locator.wait_for(state="visible", timeout=timeout)
                await locator.uncheck(timeout=timeout)
                await self._mark_success(action, selector=selector)
                return
            if action_type == "select":
                if value is None:
                    await self._mark_failed(
                        page, category_key, action_index, action_type, action,
                        "Select action için value/text bulunamadı.",
                    )
                    return
                await locator.wait_for(state="visible", timeout=timeout)
                tag_name = await locator.evaluate("(el) => el.tagName.toLowerCase()")
                select_value = str(value).strip()
                select_value_lower = select_value.lower()
                first_token = select_value.split()[0] if select_value.strip() else ""
                # Gerçek <select> elementi
                if tag_name == "select":
                    selected = False
                    # 1) doğrudan value
                    try:
                        await locator.select_option(value=select_value, timeout=timeout)
                        selected = True
                    except Exception:
                        pass
                    # 2) doğrudan label
                    if not selected:
                        try:
                            await locator.select_option(label=select_value, timeout=timeout)
                            selected = True
                        except Exception:
                            pass
                    # 3) option listesini okuyup akıllı eşleştir
                    if not selected:
                        try:
                            options = await locator.locator("option").evaluate_all(
                                """els => els.map(el => ({
                                    value: (el.value || '').trim(),
                                    label: ((el.label || el.textContent || '')).trim()
                                }))"""
                            )
                            matched_option_value = None
                            # 3a exact label
                            for opt in options:
                                if (opt.get("label") or "").strip().lower() == select_value_lower:
                                    matched_option_value = opt.get("value") or opt.get("label")
                                    break
                            # 3b exact value
                            if not matched_option_value:
                                for opt in options:
                                    if (opt.get("value") or "").strip().lower() == select_value_lower:
                                        matched_option_value = opt.get("value")
                                        break
                            # 3c contains label
                            if not matched_option_value:
                                for opt in options:
                                    label = (opt.get("label") or "").strip().lower()
                                    if select_value_lower in label or label in select_value_lower:
                                        matched_option_value = opt.get("value") or opt.get("label")
                                        break
                            # 3d first token match (örn: 150)
                            if not matched_option_value and first_token:
                                for opt in options:
                                    label = (opt.get("label") or "").strip().lower()
                                    val = (opt.get("value") or "").strip().lower()
                                    if label.startswith(first_token.lower()) or val == first_token.lower():
                                        matched_option_value = opt.get("value") or opt.get("label")
                                        break
                            if matched_option_value is not None:
                                try:
                                    await locator.select_option(value=str(matched_option_value), timeout=timeout)
                                    selected = True
                                except Exception:
                                    try:
                                        await locator.select_option(label=str(matched_option_value), timeout=timeout)
                                        selected = True
                                    except Exception:
                                        pass
                        except Exception:
                            pass
                    if not selected:
                        await self._mark_failed(
                            page, category_key, action_index, action_type, action,
                            f"Select option seçilemedi: {select_value}",
                        )
                        return
                    await self._mark_success(action, selector=selector)
                    return
                # Custom dropdown / listbox fallback
                await locator.click(timeout=timeout)
                await page.wait_for_timeout(700)
                option_locators = [
                    context.get_by_role("option", name=select_value),
                    context.get_by_role("listitem", name=select_value),
                    context.get_by_text(select_value, exact=True),
                    context.locator(f"//*[normalize-space()='{select_value}']"),
                    context.locator(f"//*[contains(normalize-space(), '{select_value}')]"),
                ]
                # ilk token fallback (örn: sadece 150)
                if first_token:
                    option_locators.extend([
                        context.get_by_text(first_token, exact=True),
                        context.locator(f"//*[starts-with(normalize-space(), '{first_token}')]"),
                        context.locator(f"//*[contains(normalize-space(), '{first_token}')]"),
                    ])
                clicked = False
                for option_locator in option_locators:
                    try:
                        count = await option_locator.count()
                        if count > 0 and await option_locator.first.is_visible():
                            await option_locator.first.click(timeout=timeout)
                            clicked = True
                            break
                    except Exception:
                        continue
                if not clicked:
                    await self._mark_failed(
                        page, category_key, action_index, action_type, action,
                        f"Select option bulunamadı: {select_value}",
                    )
                    return
                await self._mark_success(action, selector=selector)
                return
            action["status"] = "unsupported"
            action["execution_error"] = f"Desteklenmeyen action type: {action_type}"
            await self._take_failure_screenshot(page, category_key, action_index, action_type, action)
        except Exception as exc:
            await self._mark_failed(
                page, category_key, action_index, action_type, action,
                str(exc),
            )