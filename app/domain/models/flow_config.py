from __future__ import annotations
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
class BrowserExecutablePaths(BaseModel):
    chromium: Optional[str] = ""
    firefox: Optional[str] = ""
    webkit: Optional[str] = None
class GlobalSettings(BaseModel):
    browser_type: str = "chromium"
    timeout: int = 30000
    screenshot_on_failure: bool = True
    video_recording: bool = False
    attach_timeout: int = 10000
    screenshot_path: str = "REFramework/screenshots"
    last_known_url: str = ""
    initial_url: str = ""
    browser_executable_paths: BrowserExecutablePaths = Field(
        default_factory=BrowserExecutablePaths
    )
class BrowserOptions(BaseModel):
    attach_to_existing: bool = False
    browser_type: str = "chromium"
    headless: bool = False
class ActionModel(BaseModel):
    type: str
    selector: Optional[str] = None
    value: Optional[str] = None
    text: Optional[str] = None
    url: Optional[str] = None
    description: str
    prompt: str
    timeout: int = 10000
    status: str = ""
    validation_selector: Optional[str] = None
    execution_error: Optional[str] = None
    context_name: Optional[str] = None
    navigation_happened: Optional[bool] = None
    navigated_url: Optional[str] = None
    last_run_at: Optional[str] = None
    screenshot_path: Optional[str] = None
    run_count: int = 0
class CategoryModel(BaseModel):
    id: str
    name: str
    description: str
    browser_options: BrowserOptions = Field(default_factory=BrowserOptions)
    actions: List[ActionModel] = Field(default_factory=list)
class FlowItemModel(BaseModel):
    flow_name: str
    categories: Dict[str, CategoryModel] = Field(default_factory=dict)
    execution_order: List[str] = Field(default_factory=list)
    global_settings: GlobalSettings = Field(default_factory=GlobalSettings)
class ParametersModel(BaseModel):
    cyberark_domain: str = ""
    queue_db_query: str = ""
    har_recording: bool = True
    queue_name: str = ""
    dlq_queue_name: str = ""
    mongo_collection_name: str = ""
    s3_bucket_name: str = ""
    could_dchost_run: bool = False
    image_name: str = ""
    use_frontend: bool = True
    parellel_count: int = 1
    user_username: str = ""
    user_password: str = ""
    Nar_Users: List[str] = Field(default_factory=list)
    MaxRetryNumber: int = 3
    service_parameters: Dict[str, Any] = Field(default_factory=dict)
class FlowConfigRoot(BaseModel):
    flow_config: List[FlowItemModel] = Field(default_factory=list)
    parameters: ParametersModel = Field(default_factory=ParametersModel)