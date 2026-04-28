from __future__ import annotations
from app.application.use_cases.initialize_flow_config import InitializeFlowConfigUseCase
class ResetFlowConfigUseCase:
    def __init__(self) -> None:
        self._initialize_use_case = InitializeFlowConfigUseCase()
    def execute(self) -> str:
        return self._initialize_use_case.execute()