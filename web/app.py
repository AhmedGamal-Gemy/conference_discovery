"""FastAPI application entry point.

Logging must be configured before submodule imports so structlog loggers
in downstream modules use the right config.
"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from conference_agent.config import settings
from conference_agent.log_config import configure_logging

# ── Configure logging BEFORE submodule imports ──────────────────────
configure_logging(
    log_file=settings.logging.file,
    max_bytes=settings.logging.max_bytes,
    backup_count=settings.logging.backup_count,
    debug=settings.debug,
)

# ── Submodule imports below — their loggers use configured structlog ─
import structlog
from web.api import router as api_router
from web.api.pipeline import router as pipeline_router
from web.api.discovery import router as discovery_router

logger = structlog.get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Re-apply logging config after uvicorn resets it during startup."""
    configure_logging(
        log_file=settings.logging.file,
        max_bytes=settings.logging.max_bytes,
        backup_count=settings.logging.backup_count,
        debug=settings.debug,
    )
    logger = structlog.get_logger(__name__)  # noqa: F811 — refresh after re-config
    logger.info("Application starting")
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Conference Discovery", lifespan=lifespan)

    allowed_origins = [
        o.strip()
        for o in (
            __import__("os").environ.get("CORS_ORIGINS", "http://localhost:5173").split(",")
        )
        if o.strip()
    ]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(api_router, prefix="/api")
    app.include_router(pipeline_router)
    app.include_router(discovery_router, prefix="/api/discovery")

    @app.get("/health")
    def health():
        return {"status": "ok"}

    return app


app = create_app()
