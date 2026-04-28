from __future__ import annotations
import json
from app.domain.models.flow_config import (
    ActionModel,
    BrowserOptions,
    CategoryModel,
    FlowConfigRoot,
    FlowItemModel,
)
from app.domain.models.llm_models import LLMPlanResult
class BuildFlowConfigFromPlanUseCase:
    def execute(
        self,
        plan_result: LLMPlanResult,
        selected_mode: str,
        target_url: str,
        browser_type: str,
        headless: bool,
    ) -> str:
        categories_dict = {}
        for planned_category in plan_result.categories:
            actions = []
            for planned_action in planned_category.actions:
                action_type = planned_action.action_type
                action = ActionModel(
                    type=action_type,
                    selector="",
                    value=planned_action.value,
                    text=planned_action.value,
                    url=planned_action.url if planned_action.url else None,
                    description=planned_action.target_description,
                    prompt=planned_action.prompt,
                    timeout=planned_action.timeout,
                    status="draft",
                    validation_selector="",
                    execution_error=None,
                    context_name="main",
                    navigation_happened=None,
                    navigated_url=None,
                )
                if action_type == "navigate" and not action.url and target_url.strip():
                    action.url = target_url.strip()
                actions.append(action)
            categories_dict[planned_category.category_key] = CategoryModel(
                id=planned_category.category_id,
                name=planned_category.category_name,
                description=planned_category.description,
                browser_options=BrowserOptions(
                    attach_to_existing=False,
                    browser_type=browser_type,
                    headless=headless,
                ),
                actions=actions,
            )
        flow_root = FlowConfigRoot(
            flow_config=[
                FlowItemModel(
                    flow_name=plan_result.flow_name,
                    categories=categories_dict,
                    execution_order=plan_result.execution_order,
                )
            ]
        )
        return json.dumps(
            flow_root.model_dump(),
            ensure_ascii=False,
            indent=4,
        )