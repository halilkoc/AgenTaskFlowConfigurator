from pathlib import Path
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from app.presentation.web.routes.ui_routes import router as ui_router
from app.shared.config.settings import get_settings
def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        debug=settings.app_debug,
    )
    base_dir = Path(__file__).resolve().parent
    static_dir = base_dir / "presentation" / "web" / "static"
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")
    app.include_router(ui_router)
    return app
app = create_app()