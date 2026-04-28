from __future__ import annotations
from playwright.async_api import Page
class SelectorPickerService:
    PICKER_SCRIPT = r"""
(() => {
    if (window.__agentaskPickerInstalled) {
        return "already-installed";
    }
    window.__agentaskPickerInstalled = true;
    window.__agentaskPickedXPath = "";
    function getXPath(el) {
        if (!el || el.nodeType !== Node.ELEMENT_NODE) return "";
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
        return "/" + parts.join("/");
    }
    function clearHighlight(el) {
        if (!el) return;
        if (el.__agentaskOldOutline !== undefined) {
            el.style.outline = el.__agentaskOldOutline;
        } else {
            el.style.outline = "";
        }
    }
    function applyHighlight(el) {
        if (!el) return;
        if (el.__agentaskOldOutline === undefined) {
            el.__agentaskOldOutline = el.style.outline || "";
        }
        el.style.outline = "3px solid red";
    }
    let currentEl = null;
    window.__agentaskPickerMouseOver = function(event) {
        const target = event.target;
        if (!target || !(target instanceof Element)) return;
        if (currentEl && currentEl !== target) {
            clearHighlight(currentEl);
        }
        currentEl = target;
        applyHighlight(currentEl);
    };
    window.__agentaskPickerClick = function(event) {
        event.preventDefault();
        event.stopPropagation();
        event.stopImmediatePropagation();
        const target = event.target;
        if (!target || !(target instanceof Element)) return false;
        window.__agentaskPickedXPath = getXPath(target);
        document.removeEventListener("mouseover", window.__agentaskPickerMouseOver, true);
        document.removeEventListener("click", window.__agentaskPickerClick, true);
        if (currentEl) {
            clearHighlight(currentEl);
        }
        window.__agentaskPickerInstalled = false;
        return false;
    };
    document.addEventListener("mouseover", window.__agentaskPickerMouseOver, true);
    document.addEventListener("click", window.__agentaskPickerClick, true);
    return "installed";
})();
"""
    DELAYED_PICKER_SCRIPT = r"""
(delayMs) => {
    if (window.__agentaskDelayedPickerInstalled) {
        return "already-installed";
    }
    window.__agentaskDelayedPickerInstalled = true;
    window.__agentaskDelayedPickerRemaining = Math.floor((delayMs || 3000) / 1000);
    window.__agentaskDelayedPickerActive = false;
    function ensureOverlay() {
        let overlay = document.getElementById("__agentask_picker_overlay");
        if (!overlay) {
            overlay = document.createElement("div");
            overlay.id = "__agentask_picker_overlay";
            overlay.style.position = "fixed";
            overlay.style.top = "16px";
            overlay.style.right = "16px";
            overlay.style.zIndex = "2147483647";
            overlay.style.background = "rgba(0,0,0,0.85)";
            overlay.style.color = "#fff";
            overlay.style.padding = "10px 14px";
            overlay.style.borderRadius = "10px";
            overlay.style.fontSize = "14px";
            overlay.style.fontFamily = "Arial, sans-serif";
            overlay.style.boxShadow = "0 2px 10px rgba(0,0,0,0.25)";
            document.body.appendChild(overlay);
        }
        return overlay;
    }
    function setOverlayText(text) {
        const overlay = ensureOverlay();
        overlay.textContent = text;
    }
    function cleanupOverlay() {
        const overlay = document.getElementById("__agentask_picker_overlay");
        if (overlay) {
            overlay.remove();
        }
    }
    function activateRealPicker() {
        window.__agentaskDelayedPickerActive = true;
        window.__agentaskDelayedPickerInstalled = false;
        cleanupOverlay();
        if (typeof window.__agentaskStartImmediatePicker === "function") {
            window.__agentaskStartImmediatePicker();
        }
    }
    setOverlayText("Picker hazırlanıyor... F2 ile başlatıldı.");
    const timer = setInterval(() => {
        window.__agentaskDelayedPickerRemaining -= 1;
        if (window.__agentaskDelayedPickerRemaining > 0) {
            setOverlayText(
                `Picker ${window.__agentaskDelayedPickerRemaining} sn sonra aktif olacak. Önce gerekli alanı aç.`
            );
            return;
        }
        clearInterval(timer);
        setOverlayText("Picker aktif ediliyor...");
        activateRealPicker();
    }, 1000);
    return "delayed-installed";
}
"""
    START_IMMEDIATE_PICKER_HELPER = r"""
(() => {
    window.__agentaskStartImmediatePicker = function() {
        if (window.__agentaskPickerInstalled) {
            return;
        }
        window.__agentaskPickedXPath = window.__agentaskPickedXPath || "";
        function getXPath(el) {
            if (!el || el.nodeType !== Node.ELEMENT_NODE) return "";
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
            return "/" + parts.join("/");
        }
        function clearHighlight(el) {
            if (!el) return;
            if (el.__agentaskOldOutline !== undefined) {
                el.style.outline = el.__agentaskOldOutline;
            } else {
                el.style.outline = "";
            }
        }
        function applyHighlight(el) {
            if (!el) return;
            if (el.__agentaskOldOutline === undefined) {
                el.__agentaskOldOutline = el.style.outline || "";
            }
            el.style.outline = "3px solid red";
        }
        let currentEl = null;
        window.__agentaskPickerInstalled = true;
        window.__agentaskPickerMouseOver = function(event) {
            const target = event.target;
            if (!target || !(target instanceof Element)) return;
            if (currentEl && currentEl !== target) {
                clearHighlight(currentEl);
            }
            currentEl = target;
            applyHighlight(currentEl);
        };
        window.__agentaskPickerClick = function(event) {
            event.preventDefault();
            event.stopPropagation();
            event.stopImmediatePropagation();
            const target = event.target;
            if (!target || !(target instanceof Element)) return false;
            window.__agentaskPickedXPath = getXPath(target);
            document.removeEventListener("mouseover", window.__agentaskPickerMouseOver, true);
            document.removeEventListener("click", window.__agentaskPickerClick, true);
            if (currentEl) {
                clearHighlight(currentEl);
            }
            window.__agentaskPickerInstalled = false;
            return false;
        };
        document.addEventListener("mouseover", window.__agentaskPickerMouseOver, true);
        document.addEventListener("click", window.__agentaskPickerClick, true);
    };
})();
"""
    async def enable_picker(self, page: Page) -> None:
        await page.evaluate(self.START_IMMEDIATE_PICKER_HELPER)
        await page.evaluate(self.PICKER_SCRIPT)
    async def enable_delayed_picker(self, page: Page, delay_ms: int = 3000) -> None:
        await page.evaluate(self.START_IMMEDIATE_PICKER_HELPER)
        await page.evaluate(self.DELAYED_PICKER_SCRIPT, delay_ms)
    async def get_picked_selector(self, page: Page) -> str:
        result = await page.evaluate(
            "() => window.__agentaskPickedXPath ? window.__agentaskPickedXPath : ''"
        )
        return result or ""