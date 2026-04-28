from pydantic import BaseModel, Field
from typing import List, Dict, Any
class UIStateDTO(BaseModel):
    selected_mode: str = "browser"
    target_url: str = ""
    prompt_text: str = ""
    session_started: bool = False
    session_status_message: str = "Henüz oturum başlatılmadı."
    flow_config_json: str = Field(default="{}")
    browser_type: str = "chromium"
    headless: bool = False
    current_url: str = ""
    last_error: str = ""
    picked_selector: str = ""
    picker_enabled: bool = False
    available_actions: List[Dict[str, Any]] = Field(default_factory=list)
    saved_corrections: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    validation_results_json: str = "[]"
    flow_build_mode: str = "replace"
    saved_flow_files: List[Dict[str, Any]] = Field(default_factory=list)
    selected_debug_action_ref: str = ""
    action_history: List[Dict[str, Any]] = Field(default_factory=list)