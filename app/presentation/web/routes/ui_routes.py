from pathlib import Path
import logging
from fastapi import APIRouter, Request, Form
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from app.application.dto.ui_dto import UIStateDTO
from app.application.use_cases.apply_corrections_to_flow import ApplyCorrectionsToFlowUseCase
from app.application.use_cases.apply_picked_selector_to_flow import ApplyPickedSelectorToFlowUseCase
from app.application.use_cases.build_flow_config_from_plan import BuildFlowConfigFromPlanUseCase
from app.application.use_cases.clear_selector_corrections import ClearSelectorCorrectionsUseCase
from app.application.use_cases.enable_selector_picker import EnableSelectorPickerUseCase
from app.application.use_cases.execute_flow_config import ExecuteFlowConfigUseCase
from app.application.use_cases.generate_plan_from_prompt import GeneratePlanFromPromptUseCase
from app.application.use_cases.initialize_flow_config import InitializeFlowConfigUseCase
from app.application.use_cases.list_flow_actions import ListFlowActionsUseCase
from app.application.use_cases.list_selector_corrections import ListSelectorCorrectionsUseCase
from app.application.use_cases.merge_flow_configs import MergeFlowConfigsUseCase
from app.application.use_cases.read_picked_selector import ReadPickedSelectorUseCase
from app.application.use_cases.save_selector_correction import SaveSelectorCorrectionUseCase
from app.application.use_cases.start_browser_session import StartBrowserSessionUseCase
from app.application.use_cases.stop_browser_session import StopBrowserSessionUseCase
from app.application.use_cases.validate_flow_config import ValidateFlowConfigUseCase
from app.application.use_cases.validate_flow_on_page import ValidateFlowOnPageUseCase
from app.infrastructure.browser.playwright_runtime import PlaywrightBrowserRuntime
from app.infrastructure.llm.qwen_llm_client import QwenLLMClient
from app.infrastructure.persistence.file_correction_store import FileCorrectionStore
from app.infrastructure.persistence.in_memory_session_store import InMemorySessionStore
from app.application.use_cases.reset_flow_config import ResetFlowConfigUseCase
from app.application.use_cases.save_flow_config_to_file import SaveFlowConfigToFileUseCase
from app.application.use_cases.list_saved_flow_files import ListSavedFlowFilesUseCase
from app.application.use_cases.load_flow_config_from_file import LoadFlowConfigFromFileUseCase
from app.application.use_cases.execute_single_action import ExecuteSingleActionUseCase
from app.infrastructure.browser.action_history_builder import ActionHistoryBuilder
from app.application.use_cases.enable_delayed_selector_picker import EnableDelayedSelectorPickerUseCase

logger = logging.getLogger("ui_routes")
logging.basicConfig(level=logging.INFO)

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parents[1]
TEMPLATES_DIR = BASE_DIR / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

session_store = InMemorySessionStore()
initialize_flow_use_case = InitializeFlowConfigUseCase()
browser_runtime = PlaywrightBrowserRuntime()
start_browser_session_use_case = StartBrowserSessionUseCase(browser_runtime)
stop_browser_session_use_case = StopBrowserSessionUseCase(browser_runtime)
llm_client = QwenLLMClient()
generate_plan_use_case = GeneratePlanFromPromptUseCase(llm_client)
build_flow_config_use_case = BuildFlowConfigFromPlanUseCase()
execute_flow_config_use_case = ExecuteFlowConfigUseCase(browser_runtime)
validate_flow_config_use_case = ValidateFlowConfigUseCase()
validate_flow_on_page_use_case = ValidateFlowOnPageUseCase(browser_runtime)
merge_flow_configs_use_case = MergeFlowConfigsUseCase()
enable_selector_picker_use_case = EnableSelectorPickerUseCase(browser_runtime)
read_picked_selector_use_case = ReadPickedSelectorUseCase(browser_runtime)
apply_picked_selector_to_flow_use_case = ApplyPickedSelectorToFlowUseCase()
correction_store = FileCorrectionStore()
list_flow_actions_use_case = ListFlowActionsUseCase()
save_selector_correction_use_case = SaveSelectorCorrectionUseCase(correction_store)
apply_corrections_to_flow_use_case = ApplyCorrectionsToFlowUseCase(correction_store)
list_selector_corrections_use_case = ListSelectorCorrectionsUseCase(correction_store)
clear_selector_corrections_use_case = ClearSelectorCorrectionsUseCase(correction_store)
reset_flow_config_use_case = ResetFlowConfigUseCase()
save_flow_config_to_file_use_case = SaveFlowConfigToFileUseCase()
list_saved_flow_files_use_case = ListSavedFlowFilesUseCase()
load_flow_config_from_file_use_case = LoadFlowConfigFromFileUseCase()
execute_single_action_use_case = ExecuteSingleActionUseCase(browser_runtime)
action_history_builder = ActionHistoryBuilder()
enable_delayed_selector_picker_use_case = EnableDelayedSelectorPickerUseCase(browser_runtime)

def _build_ui_state() -> UIStateDTO:
    raw_state = session_store.get_state()
    if raw_state.get("flow_config_json", "{}") == "{}":
        raw_state["flow_config_json"] = initialize_flow_use_case.execute()
        session_store.update_state(flow_config_json=raw_state["flow_config_json"])
    return UIStateDTO(**raw_state)
def _render_page(request: Request) -> HTMLResponse:
    raw_state = session_store.get_state()
    flow_config_json = raw_state.get("flow_config_json", "{}")
    available_actions = []
    try:
        available_actions = list_flow_actions_use_case.execute(flow_config_json)
    except Exception:
        available_actions = []
    saved_corrections = {}
    try:
        saved_corrections = list_selector_corrections_use_case.execute()
    except Exception:
        saved_corrections = {}
    saved_flow_files = []
    try:
        saved_flow_files = list_saved_flow_files_use_case.execute()
    except Exception:
        saved_flow_files = []
    action_history = []
    try:
        action_history = action_history_builder.build(flow_config_json)
    except Exception:
        action_history = []
    session_store.update_state(
        available_actions=available_actions,
        saved_corrections=saved_corrections,
        saved_flow_files=saved_flow_files,
        action_history=action_history,
    )
    ui_state = _build_ui_state()
    return templates.TemplateResponse(
        request,
        "index.html",
        {"ui_state": ui_state},
    )
@router.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    browser_state = await browser_runtime.get_session_state()
    session_store.update_state(
        session_started=browser_state.is_running,
        current_url=browser_state.current_url,
        browser_type=browser_state.browser_type,
        headless=browser_state.headless,
        last_error=browser_state.last_error,
    )
    return _render_page(request)
@router.post("/ui/start-session", response_class=HTMLResponse)
async def start_session(
    request: Request,
    selected_mode: str = Form(...),
    target_url: str = Form(""),
    prompt_text: str = Form(""),
    browser_type: str = Form("chromium"),
    headless: str = Form("false"),
    flow_build_mode: str = Form("replace"),
) -> HTMLResponse:
    headless_bool = str(headless).lower() == "true"
    logger.info(
        "start_session | mode=%s | url=%s | browser_type=%s | headless=%s",
        selected_mode,
        target_url,
        browser_type,
        headless_bool,
    )
    try:
        if selected_mode == "desktop":
            session_store.update_state(
                selected_mode=selected_mode,
                target_url=target_url,
                prompt_text=prompt_text,
                session_started=False,
                session_status_message="Desktop modu şimdilik sadece mimari olarak hazır.",
                browser_type=browser_type,
                headless=headless_bool,
                current_url="",
                last_error="",
                flow_build_mode=flow_build_mode,
            )
        else:
            browser_state = await start_browser_session_use_case.execute(
                target_url=target_url,
                browser_type=browser_type,
                headless=headless_bool,
            )
            logger.info("Browser session sonucu: %s", browser_state)
            session_store.update_state(
                selected_mode=selected_mode,
                target_url=target_url,
                prompt_text=prompt_text,
                session_started=browser_state.is_running,
                session_status_message=browser_state.status_message,
                browser_type=browser_state.browser_type,
                headless=browser_state.headless,
                current_url=browser_state.current_url,
                last_error=browser_state.last_error,
                flow_build_mode=flow_build_mode,
            )
    except Exception as exc:
        logger.exception("start_session hata verdi")
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            session_started=False,
            session_status_message="Oturum başlatılırken hata oluştu.",
            browser_type=browser_type,
            headless=headless_bool,
            current_url="",
            last_error=str(exc),
            flow_build_mode=flow_build_mode,
        )
    return _render_page(request)
@router.post("/ui/stop-session", response_class=HTMLResponse)
async def stop_session(
    request: Request,
    selected_mode: str = Form(...),
    target_url: str = Form(""),
    prompt_text: str = Form(""),
    browser_type: str = Form("chromium"),
    headless: str = Form("false"),
    flow_build_mode: str = Form("replace"),
) -> HTMLResponse:
    headless_bool = str(headless).lower() == "true"
    logger.info("stop_session | mode=%s", selected_mode)
    try:
        if selected_mode == "browser":
            browser_state = await stop_browser_session_use_case.execute()
            session_store.update_state(
                selected_mode=selected_mode,
                target_url=target_url,
                prompt_text=prompt_text,
                session_started=browser_state.is_running,
                session_status_message=browser_state.status_message,
                browser_type=browser_state.browser_type,
                headless=browser_state.headless,
                current_url=browser_state.current_url,
                last_error=browser_state.last_error,
                flow_build_mode=flow_build_mode,
            )
        else:
            session_store.update_state(
                selected_mode=selected_mode,
                target_url=target_url,
                prompt_text=prompt_text,
                session_started=False,
                session_status_message="Desktop modu için aktif oturum bulunmuyor.",
                browser_type=browser_type,
                headless=headless_bool,
                current_url="",
                last_error="",
                flow_build_mode=flow_build_mode,
            )
    except Exception as exc:
        logger.exception("stop_session hata verdi")
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            session_status_message="Oturum sonlandırılırken hata oluştu.",
            browser_type=browser_type,
            headless=headless_bool,
            current_url="",
            last_error=str(exc),
            flow_build_mode=flow_build_mode,
        )
    return _render_page(request)
@router.post("/ui/run-prompt", response_class=HTMLResponse)
async def run_prompt(
    request: Request,
    selected_mode: str = Form(...),
    target_url: str = Form(""),
    prompt_text: str = Form(""),
    browser_type: str = Form("chromium"),
    headless: str = Form("false"),
    flow_build_mode: str = Form("replace"),
) -> HTMLResponse:
    headless_bool = str(headless).lower() == "true"
    logger.info(
        "run_prompt | mode=%s | url=%s | prompt=%s",
        selected_mode,
        target_url,
        prompt_text,
    )
    try:
        current_browser_state = await browser_runtime.get_session_state()
        if not prompt_text.strip():
            session_store.update_state(
                selected_mode=selected_mode,
                target_url=target_url,
                prompt_text=prompt_text,
                session_status_message="Prompt boş olamaz.",
                browser_type=browser_type,
                headless=headless_bool,
                last_error="",
                flow_build_mode=flow_build_mode,
            )
        elif selected_mode == "browser" and not current_browser_state.is_running:
            session_store.update_state(
                selected_mode=selected_mode,
                target_url=target_url,
                prompt_text=prompt_text,
                session_status_message="Önce browser oturumu başlatılmalı.",
                browser_type=browser_type,
                headless=headless_bool,
                last_error="",
                flow_build_mode=flow_build_mode,
            )
        else:
            plan_result = generate_plan_use_case.execute(
                user_prompt=prompt_text,
                selected_mode=selected_mode,
                target_url=target_url,
            )
            new_flow_config_json = build_flow_config_use_case.execute(
                plan_result=plan_result,
                selected_mode=selected_mode,
                target_url=target_url,
                browser_type=browser_type,
                headless=headless_bool,
            )
            current_state = session_store.get_state()
            existing_flow_config_json = current_state.get("flow_config_json", "{}")
            if flow_build_mode == "append":
                merged_flow_config_json = merge_flow_configs_use_case.execute(
                    existing_flow_config_json=existing_flow_config_json,
                    new_flow_config_json=new_flow_config_json,
                )
            else:
                merged_flow_config_json = new_flow_config_json
            merged_flow_config_json = apply_corrections_to_flow_use_case.execute(merged_flow_config_json)
            executed_flow_config_json = await execute_flow_config_use_case.execute(merged_flow_config_json)
            status_message = "Prompt işlendi ve action'lar browser üzerinde çalıştırıldı."
            if flow_build_mode == "append":
                status_message = "Yeni prompt mevcut flow config üzerine eklendi ve action'lar çalıştırıldı."
            session_store.update_state(
                selected_mode=selected_mode,
                target_url=target_url,
                prompt_text=prompt_text,
                session_status_message=status_message,
                browser_type=browser_type,
                headless=headless_bool,
                flow_config_json=executed_flow_config_json,
                flow_build_mode=flow_build_mode,
                last_error="",
            )
    except Exception as exc:
        logger.exception("run_prompt hata verdi")
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            session_status_message="Prompt işlenirken hata oluştu.",
            browser_type=browser_type,
            headless=headless_bool,
            last_error=str(exc),
            flow_build_mode=flow_build_mode,
        )
    return _render_page(request)
@router.post("/ui/replay-flow-config", response_class=HTMLResponse)
async def replay_flow_config(
    request: Request,
    selected_mode: str = Form(...),
    target_url: str = Form(""),
    prompt_text: str = Form(""),
    browser_type: str = Form("chromium"),
    headless: str = Form("false"),
    flow_config_json: str = Form(""),
    flow_build_mode: str = Form("replace"),
) -> HTMLResponse:
    headless_bool = str(headless).lower() == "true"
    try:
        current_browser_state = await browser_runtime.get_session_state()
        if selected_mode == "browser" and not current_browser_state.is_running:
            session_store.update_state(
                selected_mode=selected_mode,
                target_url=target_url,
                prompt_text=prompt_text,
                session_status_message="Replay için önce browser oturumu başlatılmalı.",
                browser_type=browser_type,
                headless=headless_bool,
                flow_config_json=flow_config_json,
                last_error="",
                flow_build_mode=flow_build_mode,
            )
            return _render_page(request)
        normalized_flow_config_json = validate_flow_config_use_case.execute(flow_config_json)
        executed_flow_config_json = await execute_flow_config_use_case.execute(normalized_flow_config_json)
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            session_status_message="Düzeltilmiş flow_config başarıyla tekrar çalıştırıldı.",
            browser_type=browser_type,
            headless=headless_bool,
            flow_config_json=executed_flow_config_json,
            last_error="",
            flow_build_mode=flow_build_mode,
        )
    except Exception as exc:
        logger.exception("replay_flow_config hata verdi")
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            session_status_message="Düzeltilmiş flow_config çalıştırılırken hata oluştu.",
            browser_type=browser_type,
            headless=headless_bool,
            flow_config_json=flow_config_json,
            last_error=str(exc),
            flow_build_mode=flow_build_mode,
        )
    return _render_page(request)
@router.post("/ui/validate-flow-config", response_class=HTMLResponse)
async def validate_flow_config(
    request: Request,
    selected_mode: str = Form(...),
    target_url: str = Form(""),
    prompt_text: str = Form(""),
    browser_type: str = Form("chromium"),
    headless: str = Form("false"),
    flow_config_json: str = Form(""),
    flow_build_mode: str = Form("replace"),
) -> HTMLResponse:
    headless_bool = str(headless).lower() == "true"
    try:
        current_browser_state = await browser_runtime.get_session_state()
        if selected_mode == "browser" and not current_browser_state.is_running:
            session_store.update_state(
                selected_mode=selected_mode,
                target_url=target_url,
                prompt_text=prompt_text,
                browser_type=browser_type,
                headless=headless_bool,
                flow_config_json=flow_config_json,
                validation_results_json="[]",
                session_status_message="Validation için önce browser oturumu başlatılmalı.",
                last_error="",
                flow_build_mode=flow_build_mode,
            )
            return _render_page(request)
        normalized_flow_config_json = validate_flow_config_use_case.execute(flow_config_json)
        validation_results_json = await validate_flow_on_page_use_case.execute(normalized_flow_config_json)
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            browser_type=browser_type,
            headless=headless_bool,
            flow_config_json=normalized_flow_config_json,
            validation_results_json=validation_results_json,
            session_status_message="Flow config doğrulama tamamlandı.",
            last_error="",
            flow_build_mode=flow_build_mode,
        )
    except Exception as exc:
        logger.exception("validate_flow_config hata verdi")
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            browser_type=browser_type,
            headless=headless_bool,
            flow_config_json=flow_config_json,
            validation_results_json="[]",
            session_status_message="Flow config doğrulanırken hata oluştu.",
            last_error=str(exc),
            flow_build_mode=flow_build_mode,
        )
    return _render_page(request)
@router.post("/ui/enable-picker", response_class=HTMLResponse)
async def enable_picker(
    request: Request,
    selected_mode: str = Form(...),
    target_url: str = Form(""),
    prompt_text: str = Form(""),
    browser_type: str = Form("chromium"),
    headless: str = Form("false"),
    flow_config_json: str = Form(""),
    flow_build_mode: str = Form("replace"),
) -> HTMLResponse:
    headless_bool = str(headless).lower() == "true"
    try:
        current_browser_state = await browser_runtime.get_session_state()
        if not current_browser_state.is_running:
            session_store.update_state(
                selected_mode=selected_mode,
                target_url=target_url,
                prompt_text=prompt_text,
                browser_type=browser_type,
                headless=headless_bool,
                flow_config_json=flow_config_json,
                session_status_message="Picker açmak için önce browser oturumu başlatılmalı.",
                last_error="",
                flow_build_mode=flow_build_mode,
            )
            return _render_page(request)
        await enable_selector_picker_use_case.execute()
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            browser_type=browser_type,
            headless=headless_bool,
            flow_config_json=flow_config_json,
            picker_enabled=True,
            session_status_message="Selector picker aktif. Browser ekranında doğru elementi tıkla.",
            last_error="",
            flow_build_mode=flow_build_mode,
        )
    except Exception as exc:
        logger.exception("enable_picker hata verdi")
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            browser_type=browser_type,
            headless=headless_bool,
            flow_config_json=flow_config_json,
            picker_enabled=False,
            session_status_message="Selector picker açılırken hata oluştu.",
            last_error=str(exc),
            flow_build_mode=flow_build_mode,
        )
    return _render_page(request)
@router.post("/ui/read-picked-selector", response_class=HTMLResponse)
async def read_picked_selector(
    request: Request,
    selected_mode: str = Form(...),
    target_url: str = Form(""),
    prompt_text: str = Form(""),
    browser_type: str = Form("chromium"),
    headless: str = Form("false"),
    flow_config_json: str = Form(""),
    flow_build_mode: str = Form("replace"),
) -> HTMLResponse:
    headless_bool = str(headless).lower() == "true"
    try:
        picked_selector = await read_picked_selector_use_case.execute()
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            browser_type=browser_type,
            headless=headless_bool,
            flow_config_json=flow_config_json,
            picked_selector=picked_selector,
            picker_enabled=False,
            session_status_message="Seçilen selector okundu.",
            last_error="",
            flow_build_mode=flow_build_mode,
        )
    except Exception as exc:
        logger.exception("read_picked_selector hata verdi")
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            browser_type=browser_type,
            headless=headless_bool,
            flow_config_json=flow_config_json,
            picker_enabled=False,
            session_status_message="Seçilen selector okunurken hata oluştu.",
            last_error=str(exc),
            flow_build_mode=flow_build_mode,
        )
    return _render_page(request)
@router.post("/ui/apply-picked-selector", response_class=HTMLResponse)
async def apply_picked_selector(
    request: Request,
    selected_mode: str = Form(...),
    target_url: str = Form(""),
    prompt_text: str = Form(""),
    browser_type: str = Form("chromium"),
    headless: str = Form("false"),
    flow_config_json: str = Form(""),
    picked_selector: str = Form(""),
    target_category_key: str = Form(""),
    target_action_index: int = Form(...),
    flow_build_mode: str = Form("replace"),
) -> HTMLResponse:
    headless_bool = str(headless).lower() == "true"
    try:
        updated_flow_config_json = apply_picked_selector_to_flow_use_case.execute(
            flow_config_json=flow_config_json,
            picked_selector=picked_selector,
            target_category_key=target_category_key,
            target_action_index=target_action_index,
        )
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            browser_type=browser_type,
            headless=headless_bool,
            flow_config_json=updated_flow_config_json,
            picked_selector=picked_selector,
            session_status_message="Seçilen selector flow_config içine uygulandı.",
            last_error="",
            flow_build_mode=flow_build_mode,
        )
    except Exception as exc:
        logger.exception("apply_picked_selector hata verdi")
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            browser_type=browser_type,
            headless=headless_bool,
            flow_config_json=flow_config_json,
            picked_selector=picked_selector,
            session_status_message="Seçilen selector config'e uygulanırken hata oluştu.",
            last_error=str(exc),
            flow_build_mode=flow_build_mode,
        )
    return _render_page(request)
@router.post("/ui/apply-picked-selector-by-choice", response_class=HTMLResponse)
async def apply_picked_selector_by_choice(
    request: Request,
    selected_mode: str = Form(...),
    target_url: str = Form(""),
    prompt_text: str = Form(""),
    browser_type: str = Form("chromium"),
    headless: str = Form("false"),
    flow_config_json: str = Form(""),
    picked_selector: str = Form(""),
    selected_action_ref: str = Form(""),
    flow_build_mode: str = Form("replace"),
) -> HTMLResponse:
    headless_bool = str(headless).lower() == "true"
    try:
        if not selected_action_ref.strip():
            raise ValueError("Uygulanacak action seçilmedi.")
        parts = selected_action_ref.split("::")
        if len(parts) != 2:
            raise ValueError("Action referansı geçersiz.")
        target_category_key = parts[0]
        target_action_index = int(parts[1])
        updated_flow_config_json = apply_picked_selector_to_flow_use_case.execute(
            flow_config_json=flow_config_json,
            picked_selector=picked_selector,
            target_category_key=target_category_key,
            target_action_index=target_action_index,
        )
        actions = list_flow_actions_use_case.execute(updated_flow_config_json)
        selected_action = next(
            (
                item for item in actions
                if item["category_key"] == target_category_key and item["action_index"] == target_action_index
            ),
            None,
        )
        if selected_action:
            save_selector_correction_use_case.execute(
                action_type=selected_action["action_type"],
                description=selected_action["description"],
                selector=picked_selector,
                context_name="main",
            )
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            browser_type=browser_type,
            headless=headless_bool,
            flow_config_json=updated_flow_config_json,
            picked_selector=picked_selector,
            session_status_message="Seçilen selector action'a uygulandı ve düzeltme hafızaya alındı.",
            last_error="",
            flow_build_mode=flow_build_mode,
        )
    except Exception as exc:
        logger.exception("apply_picked_selector_by_choice hata verdi")
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            browser_type=browser_type,
            headless=headless_bool,
            flow_config_json=flow_config_json,
            picked_selector=picked_selector,
            session_status_message="Selector action'a uygulanırken hata oluştu.",
            last_error=str(exc),
            flow_build_mode=flow_build_mode,
        )
    return _render_page(request)
@router.post("/ui/clear-selector-corrections", response_class=HTMLResponse)
async def clear_selector_corrections(
    request: Request,
    selected_mode: str = Form(...),
    target_url: str = Form(""),
    prompt_text: str = Form(""),
    browser_type: str = Form("chromium"),
    headless: str = Form("false"),
    flow_config_json: str = Form(""),
    flow_build_mode: str = Form("replace"),
) -> HTMLResponse:
    headless_bool = str(headless).lower() == "true"
    try:
        clear_selector_corrections_use_case.execute()
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            browser_type=browser_type,
            headless=headless_bool,
            flow_config_json=flow_config_json,
            session_status_message="Kaydedilmiş selector düzeltmeleri temizlendi.",
            last_error="",
            flow_build_mode=flow_build_mode,
        )
    except Exception as exc:
        logger.exception("clear_selector_corrections hata verdi")
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            browser_type=browser_type,
            headless=headless_bool,
            flow_config_json=flow_config_json,
            session_status_message="Selector düzeltmeleri temizlenirken hata oluştu.",
            last_error=str(exc),
            flow_build_mode=flow_build_mode,
        )
    return _render_page(request)
@router.post("/ui/reset-flow-config", response_class=HTMLResponse)
async def reset_flow_config(
    request: Request,
    selected_mode: str = Form(...),
    target_url: str = Form(""),
    prompt_text: str = Form(""),
    browser_type: str = Form("chromium"),
    headless: str = Form("false"),
    flow_build_mode: str = Form("replace"),
) -> HTMLResponse:
    headless_bool = str(headless).lower() == "true"
    try:
        new_flow_config_json = reset_flow_config_use_case.execute()
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text="",
            browser_type=browser_type,
            headless=headless_bool,
            flow_config_json=new_flow_config_json,
            validation_results_json="[]",
            picked_selector="",
            session_status_message="Yeni akış başlatıldı. Flow config sıfırlandı.",
            last_error="",
            flow_build_mode=flow_build_mode,
        )
    except Exception as exc:
        logger.exception("reset_flow_config hata verdi")
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            browser_type=browser_type,
            headless=headless_bool,
            session_status_message="Flow config sıfırlanırken hata oluştu.",
            last_error=str(exc),
            flow_build_mode=flow_build_mode,
        )
    return _render_page(request)
@router.post("/ui/save-flow-config", response_class=HTMLResponse)
async def save_flow_config(
    request: Request,
    selected_mode: str = Form(...),
    target_url: str = Form(""),
    prompt_text: str = Form(""),
    browser_type: str = Form("chromium"),
    headless: str = Form("false"),
    flow_config_json: str = Form(""),
    flow_build_mode: str = Form("replace"),
    save_file_name: str = Form(""),
) -> HTMLResponse:
    headless_bool = str(headless).lower() == "true"
    try:
        normalized_flow_config_json = validate_flow_config_use_case.execute(flow_config_json)
        saved_file_path = save_flow_config_to_file_use_case.execute(
            flow_config_json=normalized_flow_config_json,
            file_name=save_file_name,
        )
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            browser_type=browser_type,
            headless=headless_bool,
            flow_config_json=normalized_flow_config_json,
            session_status_message=f"Flow config kaydedildi: {saved_file_path}",
            last_error="",
            flow_build_mode=flow_build_mode,
        )
    except Exception as exc:
        logger.exception("save_flow_config hata verdi")
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            browser_type=browser_type,
            headless=headless_bool,
            flow_config_json=flow_config_json,
            session_status_message="Flow config kaydedilirken hata oluştu.",
            last_error=str(exc),
            flow_build_mode=flow_build_mode,
        )
    return _render_page(request)
@router.post("/ui/load-flow-config", response_class=HTMLResponse)
async def load_flow_config(
    request: Request,
    selected_mode: str = Form(...),
    target_url: str = Form(""),
    prompt_text: str = Form(""),
    browser_type: str = Form("chromium"),
    headless: str = Form("false"),
    flow_build_mode: str = Form("replace"),
    selected_saved_flow_file: str = Form(""),
) -> HTMLResponse:
    headless_bool = str(headless).lower() == "true"
    try:
        loaded_flow_config_json = load_flow_config_from_file_use_case.execute(selected_saved_flow_file)
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            browser_type=browser_type,
            headless=headless_bool,
            flow_config_json=loaded_flow_config_json,
            validation_results_json="[]",
            picked_selector="",
            session_status_message=f"Flow config yüklendi: {selected_saved_flow_file}",
            last_error="",
            flow_build_mode=flow_build_mode,
        )
    except Exception as exc:
        logger.exception("load_flow_config hata verdi")
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            browser_type=browser_type,
            headless=headless_bool,
            session_status_message="Flow config yüklenirken hata oluştu.",
            last_error=str(exc),
            flow_build_mode=flow_build_mode,
        )
    return _render_page(request)
@router.post("/ui/run-single-action", response_class=HTMLResponse)
async def run_single_action(
    request: Request,
    selected_mode: str = Form(...),
    target_url: str = Form(""),
    prompt_text: str = Form(""),
    browser_type: str = Form("chromium"),
    headless: str = Form("false"),
    flow_build_mode: str = Form("replace"),
    flow_config_json: str = Form(""),
    selected_debug_action_ref: str = Form(""),
) -> HTMLResponse:
    headless_bool = str(headless).lower() == "true"
    try:
        current_browser_state = await browser_runtime.get_session_state()
        if selected_mode == "browser" and not current_browser_state.is_running:
            session_store.update_state(
                selected_mode=selected_mode,
                target_url=target_url,
                prompt_text=prompt_text,
                browser_type=browser_type,
                headless=headless_bool,
                flow_config_json=flow_config_json,
                selected_debug_action_ref=selected_debug_action_ref,
                session_status_message="Tek action çalıştırmak için önce browser oturumu başlatılmalı.",
                last_error="",
                flow_build_mode=flow_build_mode,
            )
            return _render_page(request)
        if not selected_debug_action_ref.strip():
            raise ValueError("Çalıştırılacak action seçilmedi.")
        parts = selected_debug_action_ref.split("::")
        if len(parts) != 2:
            raise ValueError("Action referansı geçersiz.")
        category_key = parts[0]
        action_index = int(parts[1])
        normalized_flow_config_json = validate_flow_config_use_case.execute(flow_config_json)
        updated_flow_config_json = await execute_single_action_use_case.execute(
            flow_config_json=normalized_flow_config_json,
            category_key=category_key,
            action_index=action_index,
        )
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            browser_type=browser_type,
            headless=headless_bool,
            flow_config_json=updated_flow_config_json,
            selected_debug_action_ref=selected_debug_action_ref,
            session_status_message="Seçilen action başarıyla çalıştırıldı.",
            last_error="",
            flow_build_mode=flow_build_mode,
        )
    except Exception as exc:
        logger.exception("run_single_action hata verdi")
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            browser_type=browser_type,
            headless=headless_bool,
            flow_config_json=flow_config_json,
            selected_debug_action_ref=selected_debug_action_ref,
            session_status_message="Seçilen action çalıştırılırken hata oluştu.",
            last_error=str(exc),
            flow_build_mode=flow_build_mode,
        )
    return _render_page(request)
@router.post("/ui/enable-delayed-picker", response_class=HTMLResponse)
async def enable_delayed_picker(
    request: Request,
    selected_mode: str = Form(...),
    target_url: str = Form(""),
    prompt_text: str = Form(""),
    browser_type: str = Form("chromium"),
    headless: str = Form("false"),
    flow_config_json: str = Form(""),
    flow_build_mode: str = Form("replace"),
    picker_delay_seconds: int = Form(3),
) -> HTMLResponse:
    headless_bool = str(headless).lower() == "true"
    try:
        current_browser_state = await browser_runtime.get_session_state()
        if not current_browser_state.is_running:
            session_store.update_state(
                selected_mode=selected_mode,
                target_url=target_url,
                prompt_text=prompt_text,
                browser_type=browser_type,
                headless=headless_bool,
                flow_config_json=flow_config_json,
                session_status_message="Gecikmeli picker için önce browser oturumu başlatılmalı.",
                last_error="",
                flow_build_mode=flow_build_mode,
            )
            return _render_page(request)
        delay_ms = max(1, picker_delay_seconds) * 1000
        await enable_delayed_selector_picker_use_case.execute(delay_ms=delay_ms)
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            browser_type=browser_type,
            headless=headless_bool,
            flow_config_json=flow_config_json,
            picker_enabled=True,
            session_status_message=f"Gecikmeli picker aktif. {picker_delay_seconds} saniye içinde gerekli alanı aç, sonra hedef elementi seç.",
            last_error="",
            flow_build_mode=flow_build_mode,
        )
    except Exception as exc:
        logger.exception("enable_delayed_picker hata verdi")
        session_store.update_state(
            selected_mode=selected_mode,
            target_url=target_url,
            prompt_text=prompt_text,
            browser_type=browser_type,
            headless=headless_bool,
            flow_config_json=flow_config_json,
            picker_enabled=False,
            session_status_message="Gecikmeli picker açılırken hata oluştu.",
            last_error=str(exc),
            flow_build_mode=flow_build_mode,
        )
    return _render_page(request)