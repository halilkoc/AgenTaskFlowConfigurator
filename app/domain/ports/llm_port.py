from __future__ import annotations
from abc import ABC, abstractmethod
from app.domain.models.llm_models import LLMPlanResult
class LLMPort(ABC):
    @abstractmethod
    def generate_plan(
        self,
        user_prompt: str,
        selected_mode: str,
        target_url: str,
    ) -> LLMPlanResult:
        raise NotImplementedError