from __future__ import annotations
from typing import List, Optional
from pydantic import BaseModel, Field
class PlannedAction(BaseModel):
    action_type: str
    target_description: str
    value: Optional[str] = None
    url: Optional[str] = None
    prompt: str
    timeout: int = 10000
class PlannedCategory(BaseModel):
    category_key: str
    category_id: str
    category_name: str
    description: str
    actions: List[PlannedAction] = Field(default_factory=list)
class LLMPlanResult(BaseModel):
    flow_name: str
    categories: List[PlannedCategory] = Field(default_factory=list)
    execution_order: List[str] = Field(default_factory=list)
    raw_text: str = ""