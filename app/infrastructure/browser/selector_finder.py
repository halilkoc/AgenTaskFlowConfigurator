from __future__ import annotations
from typing import Any, Dict, List, Optional
from playwright.async_api import Page
from app.infrastructure.browser.dom_snapshot import DOMSnapshotService
from app.infrastructure.browser.page_context_service import PageContextService
from app.infrastructure.browser.xpath_builder import XPathBuilder
class SelectorFinder:
    def __init__(self) -> None:
        self._dom_snapshot_service = DOMSnapshotService()
        self._xpath_builder = XPathBuilder()
        self._page_context_service = PageContextService()
    async def find_selector_for_action(
        self,
        page: Page,
        action_type: str,
        description: str,
        prompt: str,
        value: str | None = None,
    ) -> dict[str, str]:
        all_contexts = await self._page_context_service.get_all_contexts(page)
        all_elements: List[Dict[str, Any]] = []
        for context_name, context in all_contexts:
            elements = await self._dom_snapshot_service.capture_interactive_elements(
                context=context,
                context_name=context_name,
            )
            all_elements.extend(elements)
        best_element = self._find_best_element(
            elements=all_elements,
            action_type=action_type,
            description=description,
            prompt=prompt,
            value=value,
        )
        if not best_element:
            return {"selector": "", "context_name": "main"}
        return {
            "selector": self._xpath_builder.build_best_xpath(best_element),
            "context_name": best_element.get("context_name", "main"),
        }
    def _find_best_element(
        self,
        elements: List[Dict[str, Any]],
        action_type: str,
        description: str,
        prompt: str,
        value: str | None = None,
    ) -> Optional[Dict[str, Any]]:
        scored: List[tuple[int, Dict[str, Any]]] = []
        desc = (description or "").lower()
        prm = (prompt or "").lower()
        val = (value or "").lower()
        combined = f"{desc} {prm} {val}"
        for element in elements:
            score = self._score_element(
                element=element,
                action_type=action_type,
                combined_text=combined,
            )
            if score > 0:
                scored.append((score, element))
        if not scored:
            return None
        scored.sort(key=lambda item: item[0], reverse=True)
        return scored[0][1]
    def _score_element(
        self,
        element: Dict[str, Any],
        action_type: str,
        combined_text: str,
    ) -> int:
        score = 0
        tag = (element.get("tag") or "").lower()
        input_type = (element.get("type") or "").lower()
        name = (element.get("name") or "").lower()
        element_id = (element.get("id") or "").lower()
        placeholder = (element.get("placeholder") or "").lower()
        aria_label = (element.get("aria_label") or "").lower()
        label_text = (element.get("label_text") or "").lower()
        title = (element.get("title") or "").lower()
        text = (element.get("text") or "").lower()
        role = (element.get("role") or "").lower()
        value_attr = (element.get("value") or "").lower()
        searchable = " ".join([
            tag,
            input_type,
            name,
            element_id,
            placeholder,
            aria_label,
            label_text,
            title,
            text,
            role,
            value_attr,
        ])
        if action_type in {"fill", "type", "focus_and_fill"}:
            score += self._score_text_input_like_element(
                tag=tag,
                input_type=input_type,
                searchable=searchable,
                combined_text=combined_text,
            )
        if action_type == "click":
            score += self._score_clickable_element(
                tag=tag,
                input_type=input_type,
                role=role,
                searchable=searchable,
                combined_text=combined_text,
            )
        if action_type == "select":
            score += self._score_selectable_element(
                tag=tag,
                input_type=input_type,
                role=role,
                searchable=searchable,
                combined_text=combined_text,
            )
        if action_type == "wait":
            score += self._score_wait_target(
                tag=tag,
                input_type=input_type,
                role=role,
                searchable=searchable,
                combined_text=combined_text,
            )
        return score
    def _score_text_input_like_element(
        self,
        tag: str,
        input_type: str,
        searchable: str,
        combined_text: str,
    ) -> int:
        score = 0
        if tag in {"input", "textarea", "select"}:
            score += 20
        if input_type in {"text", "email", "password", "search", "number"}:
            score += 20
        # password
        if any(keyword in combined_text for keyword in ["password", "şifre", "sifre", "parola"]):
            if "password" in searchable:
                score += 120
            if input_type == "password":
                score += 180
            if any(keyword in searchable for keyword in ["şifre", "sifre", "parola"]):
                score += 100
        # username / user / sicil
        if any(keyword in combined_text for keyword in ["username", "kullanıcı", "kullanici", "user", "sicil"]):
            if any(keyword in searchable for keyword in ["username", "user", "userid", "kullanıcı", "kullanici", "sicil"]):
                score += 150
            if input_type in {"text", "email"}:
                score += 40
        # email
        if any(keyword in combined_text for keyword in ["email", "e-mail", "eposta", "mail"]):
            if any(keyword in searchable for keyword in ["email", "e-mail", "eposta", "mail"]):
                score += 130
            if input_type == "email":
                score += 100
        # search
        if any(keyword in combined_text for keyword in ["ara", "arama", "search", "bul"]):
            if any(keyword in searchable for keyword in ["ara", "arama", "search", "bul"]):
                score += 120
            if input_type == "search":
                score += 120
        # branch / şube
        if any(keyword in combined_text for keyword in ["şube", "sube", "branch"]):
            if any(keyword in searchable for keyword in ["şube", "sube", "branch"]):
                score += 120
        # process / işlem no
        if any(keyword in combined_text for keyword in ["işlem", "islem", "process", "transaction", "no"]):
            if any(keyword in searchable for keyword in ["işlem", "islem", "process", "transaction", "no", "id"]):
                score += 60
        return score
    def _score_clickable_element(
        self,
        tag: str,
        input_type: str,
        role: str,
        searchable: str,
        combined_text: str,
    ) -> int:
        score = 0
        if tag in {"button", "a"} or role == "button" or input_type in {"submit", "button"}:
            score += 30
        # login / giriş yap
        if "giriş yap" in combined_text or "giris yap" in combined_text:
            if any(keyword in searchable for keyword in ["giriş yap", "giris yap", "login", "sign in", "log in"]):
                score += 180
        if "login" in combined_text:
            if any(keyword in searchable for keyword in ["login", "sign in", "log in", "giriş yap", "giris yap"]):
                score += 180
        # devam
        if "devam" in combined_text and "devam" in searchable:
            score += 160
        # ara / search
        if any(keyword in combined_text for keyword in ["ara", "arama", "search", "bul"]):
            if any(keyword in searchable for keyword in ["ara", "arama", "search", "bul", "search icon"]):
                score += 140
        # aç / open / seç
        if any(keyword in combined_text for keyword in ["aç", "ac", "open", "seç", "sec", "choose"]):
            if any(keyword in searchable for keyword in ["aç", "ac", "open", "seç", "sec", "choose"]):
                score += 100
        # logout / çıkış
        if any(keyword in combined_text for keyword in ["çıkış", "cikis", "logout", "sign out"]):
            if any(keyword in searchable for keyword in ["çıkış", "cikis", "logout", "sign out"]):
                score += 180
        return score
    def _score_selectable_element(
        self,
        tag: str,
        input_type: str,
        role: str,
        searchable: str,
        combined_text: str,
    ) -> int:
        score = 0
        if tag == "select":
            score += 220
        if tag in {"input", "button", "div", "span", "li"}:
            score += 15
        if role in {"combobox", "listbox", "option", "button"}:
            score += 120
        if any(keyword in combined_text for keyword in ["şube", "sube", "branch"]):
            if any(keyword in searchable for keyword in ["şube", "sube", "branch"]):
                score += 170
        if any(keyword in combined_text for keyword in ["dropdown", "liste", "list", "option", "seç", "sec", "select"]):
            if any(keyword in searchable for keyword in ["dropdown", "liste", "list", "option", "seç", "sec", "select"]):
                score += 150
        if any(keyword in combined_text for keyword in ["menü", "menu", "açılır", "acilir"]):
            if any(keyword in searchable for keyword in ["menü", "menu", "açılır", "acilir"]):
                score += 120
        if input_type in {"text", "search"} and any(keyword in combined_text for keyword in ["seç", "sec", "select"]):
            score += 40
        return score
    def _score_wait_target(
        self,
        tag: str,
        input_type: str,
        role: str,
        searchable: str,
        combined_text: str,
    ) -> int:
        score = 0
        if tag in {"div", "span", "button", "a", "input"}:
            score += 10
        if role:
            score += 10
        if any(keyword in combined_text for keyword in ["yüklen", "yuklen", "hazır", "hazir", "visible", "görün", "gorun", "bekle", "wait"]):
            score += 50
        if any(keyword in searchable for keyword in combined_text.split()):
            score += 20
        return score