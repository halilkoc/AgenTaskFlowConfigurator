import json
from app.domain.models.flow_config import FlowConfigRoot, FlowItemModel
class InitializeFlowConfigUseCase:
    def execute(self) -> str:
        initial_config = FlowConfigRoot(
            flow_config=[
                FlowItemModel(
                    flow_name="Yeni_Akıs",
                )
            ]
        )
        return json.dumps(
            initial_config.model_dump(),
            ensure_ascii=False,
            indent=4
        )