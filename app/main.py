from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi_offline import FastAPIOffline
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from . import api, web
from .config import ROOT, Settings
from .db import open_database
from .dependencies import Db
from .domain import DomainError
from .models import Base


def create_app(settings: Settings | None = None) -> FastAPI:
    settings = settings or Settings.from_env()
    engine = open_database(settings.database_path)

    @asynccontextmanager
    async def lifespan(_app: FastAPI):
        try:
            settings.database_path.parent.mkdir(parents=True, exist_ok=True)
            Base.metadata.create_all(engine)
            yield
        finally:
            engine.dispose()

    app = FastAPIOffline(
        title="CampusRide QA Lab",
        version="0.1.0",
        description="Fictional campus rides. Sign in through the app or the login endpoint to test protected routes.",
        redoc_url=None,
        lifespan=lifespan,
        swagger_ui_parameters={"validatorUrl": None},
    )
    app.state.settings = settings
    app.state.engine = engine
    app.mount("/static", StaticFiles(directory=ROOT / "app" / "static"), name="static")

    @app.middleware("http")
    async def prevent_caching_api_responses(request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/api/"):
            response.headers["Cache-Control"] = "no-store"
        return response

    @app.exception_handler(DomainError)
    async def handle_domain_error(request: Request, error: DomainError):
        if request.url.path.startswith("/api/"):
            return JSONResponse({"detail": str(error)}, status_code=error.status_code)
        if error.status_code == 401:
            return RedirectResponse("/login", status_code=303)
        return web.render(request, "error.html", status_code=error.status_code, message=str(error))

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, error: RequestValidationError):
        if not request.url.path.startswith("/api/"):
            return web.render(request, "error.html", status_code=422, message="That page address is invalid.")
        # Validation errors must never echo submitted credentials or other input values.
        details = [{key: issue[key] for key in ("loc", "msg", "type")} for issue in error.errors()]
        return JSONResponse({"detail": details}, status_code=422)

    @app.get("/health", tags=["System"])
    def health(db: Db):
        try:
            db.execute(text("SELECT 1"))
        except SQLAlchemyError:
            return JSONResponse({"status": "unavailable"}, status_code=503)
        return {"status": "ok"}

    app.include_router(api.router)
    app.include_router(web.router)
    return app


app = create_app()
