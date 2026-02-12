from fastapi import FastAPI
from .settings import settings
from .db import init_db
from .routes.decision import router as decision_router
from .routes.explain import router as explain_router
from .routes.review import router as review_router

def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    from prometheus_fastapi_instrumentator import Instrumentator
    Instrumentator().instrument(app).expose(app)

    @app.on_event("startup")
    def _startup():
        init_db()

    app.include_router(decision_router)
    app.include_router(explain_router)
    app.include_router(review_router)
    return app

app = create_app()
