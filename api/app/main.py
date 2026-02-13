from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .settings import settings
from .db import init_db
from .routes.decision import router as decision_router
from .routes.explain import router as explain_router
from .routes.review import router as review_router
from .routes.ui import router as ui_router

BASE_DIR = Path(__file__).resolve().parent

def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    # Fichiers statiques (CSS, JS, images)
    app.mount("/static", StaticFiles(directory=str(BASE_DIR / "static")), name="static")

    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app)

    @app.on_event("startup")
    def _startup():
        init_db()

    # API routes
    app.include_router(decision_router)
    app.include_router(explain_router)
    app.include_router(review_router)

    # Routes UI (doit être en dernier pour ne pas masquer les routes API)
    app.include_router(ui_router)

    return app

app = create_app()
