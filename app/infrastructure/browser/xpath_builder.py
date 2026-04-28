from __future__ import annotations
from typing import Any, Dict
class XPathBuilder:
    def build_best_xpath(self, element: Dict[str, Any]) -> str:
        element_id = (element.get("id") or "").strip()
        name = (element.get("name") or "").strip()
        tag = (element.get("tag") or "").strip()
        input_type = (element.get("type") or "").strip()
        placeholder = (element.get("placeholder") or "").strip()
        aria_label = (element.get("aria_label") or "").strip()
        label_text = (element.get("label_text") or "").strip()
        text = (element.get("text") or "").strip()
        raw_xpath = (element.get("xpath") or "").strip()
        if element_id:
            return f'//*[@id="{element_id}"]'
        if tag and name:
            return f'//{tag}[@name="{name}"]'
        if tag and aria_label:
            return f'//{tag}[@aria-label="{aria_label}"]'
        if tag and placeholder:
            return f'//{tag}[@placeholder="{placeholder}"]'
        if tag and input_type == "password":
            return f'//{tag}[@type="password"]'
        if tag == "button" and text:
            return f'//button[normalize-space()="{text}"]'
        if tag == "a" and text:
            return f'//a[normalize-space()="{text}"]'
        if label_text and raw_xpath:
            return raw_xpath
        if raw_xpath:
            return raw_xpath
        return ""