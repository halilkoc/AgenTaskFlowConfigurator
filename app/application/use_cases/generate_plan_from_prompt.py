from __future__ import annotations
from app.domain.models.llm_models import LLMPlanResult
from app.domain.ports.llm_port import LLMPort
class GeneratePlanFromPromptUseCase:
    def __init__(self, llm_port: LLMPort) -> None:
        self._llm_port = llm_port
    def execute(
        self,
        user_prompt: str,
        selected_mode: str,
        target_url: str,
    ) -> LLMPlanResult:
        return self._llm_port.generate_plan(
            user_prompt=user_prompt,
            selected_mode=selected_mode,
            target_url=target_url,
        )