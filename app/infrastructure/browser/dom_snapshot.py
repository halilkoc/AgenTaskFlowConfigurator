from __future__ import annotations
from typing import Any, Dict, List
from playwright.async_api import Frame, Page
class DOMSnapshotService:
    async def capture_interactive_elements(
        self,
        context: Page | Frame,
        context_name: str = "main",
    ) -> List[Dict[str, Any]]:
        js_script = """
        () => {
            function isVisible(el) {
                if (!el) return false;
                const style = window.getComputedStyle(el);
                const rect = el.getBoundingClientRect();
                return (
                    style &&
                    style.visibility !== 'hidden' &&
                    style.display !== 'none' &&
                    rect.width > 0 &&
                    rect.height > 0
                );
            }
            function getXPath(el) {
                if (!el || el.nodeType !== Node.ELEMENT_NODE) return '';
                if (el.id) {
                    return `//*[@id="${el.id}"]`;
                }
                const parts = [];
                while (el && el.nodeType === Node.ELEMENT_NODE) {
                    let index = 1;
                    let sibling = el.previousElementSibling;
                    while (sibling) {
                        if (sibling.tagName === el.tagName) {
                            index++;
                        }
                        sibling = sibling.previousElementSibling;
                    }
                    parts.unshift(`${el.tagName.toLowerCase()}[${index}]`);
                    el = el.parentElement;
                }
                return '/' + parts.join('/');
            }
            function cleanText(text) {
                return (text || '').replace(/\\s+/g, ' ').trim();
            }
            function getRole(el) {
                return el.getAttribute('role') || '';
            }
            function getLabelText(el) {
                if (!el) return '';
                const ariaLabel = el.getAttribute('aria-label');
                if (ariaLabel) return cleanText(ariaLabel);
                const id = el.id || '';
                if (id) {
                    const explicit = document.querySelector(`label[for="${id}"]`);
                    if (explicit) return cleanText(explicit.innerText || explicit.textContent || '');
                }
                let parent = el.parentElement;
                while (parent) {
                    if (parent.tagName && parent.tagName.toLowerCase() === 'label') {
                        return cleanText(parent.innerText || parent.textContent || '');
                    }
                    parent = parent.parentElement;
                }
                return '';
            }
            const selector = `
                input, textarea, select, button, a,
                [role="button"], [role="textbox"], [contenteditable="true"]
            `;
            const elements = Array.from(document.querySelectorAll(selector));
            return elements
                .filter(el => isVisible(el))
                .map((el, index) => ({
                    index,
                    tag: (el.tagName || '').toLowerCase(),
                    type: el.getAttribute('type') || '',
                    id: el.id || '',
                    name: el.getAttribute('name') || '',
                    placeholder: el.getAttribute('placeholder') || '',
                    aria_label: el.getAttribute('aria-label') || '',
                    title: el.getAttribute('title') || '',
                    role: getRole(el),
                    label_text: getLabelText(el),
                    text: cleanText(el.innerText || el.textContent || ''),
                    value: el.getAttribute('value') || '',
                    xpath: getXPath(el),
                    css_selector: el.id ? `#${el.id}` : '',
                }));
        }
        """
        result = await context.evaluate(js_script)
        items = result if isinstance(result, list) else []
        for item in items:
            item["context_name"] = context_name
        return items