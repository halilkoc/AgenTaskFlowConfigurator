from __future__ import annotations
from threading import Lock
from typing import Dict, Any
class InMemorySessionStore:
    def __init__(self) -> None:
        self._lock = Lock()
        self._state: Dict[str, Any] = {
            "selected_mode": "browser",
            "target_url": "",
            "prompt_text": "",
            "session_started": False,
            "session_status_message": "Henüz oturum başlatılmadı.",
            "flow_config_json": "{}",
            "browser_type": "chromium",
            "headless": False,
            "current_url": "",
            "last_error": "",
            "picked_selector": "",
            "picker_enabled": False,
            "available_actions": [],
            "saved_corrections": {},
            "validation_results_json": "[]",
            "flow_build_mode": "replace",
            "saved_flow_files": [],
            "selected_debug_action_ref": "",
            "action_history": [],
        }
    def get_state(self) -> Dict[str, Any]:
        with self._lock:
            return dict(self._state)
    def update_state(self, **kwargs: Any) -> Dict[str, Any]:
        with self._lock:
            self._state.update(kwargs)
            return dict(self._state)