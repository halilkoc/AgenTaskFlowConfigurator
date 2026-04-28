from __future__ import annotations
from pydantic import BaseModel, Field
class BrowserSessionState(BaseModel):
    is_running: bool = False
    current_url: str = ""
    browser_type: str = "chromium"
    headless: bool = False
    status_message: str = "Henüz browser oturumu başlatılmadı."
    last_error: str = ""
    session_id: str = Field(default="default-browser-session")