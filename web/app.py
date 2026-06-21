import logging
import os
import sys

import structlog
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from web.api import router as api_router
from web.api.pipeline import router as pipeline_router
from web.api.discovery import router as discovery_router

from conference_agent.config import settings

_log_level = logging.DEBUG if (settings.debug or "--debug" in sys.argv) else logging.INFO

# ── Detect environment ────────────────────────────────────────────────
# TTY → pretty console colors, pipe/Docker → structured JSON
_use_json = not sys.stderr.isatty()

# ── Shared processors (run before the final renderer) ─────────────────

_shared_processors = [
    structlog.stdlib.add_logger_name,
    structlog.stdlib.add_log_level,
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.processors.TimeStamper(fmt="%H:%M:%S"),
    structlog.processors.StackInfoRenderer(),
    structlog.processors.format_exc_info,
]

# ── Configure structlog natively (for structlog-native loggers) ───────

structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        *_shared_processors,
        structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
    ],
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

# ── Bridge structlog → stdlib (so existing logger.info() calls work) ──

_renderer = (
    structlog.processors.JSONRenderer()
    if _use_json
    else structlog.dev.ConsoleRenderer()
)

_handler = logging.StreamHandler(stream=sys.stdout)
_handler.setFormatter(
    structlog.stdlib.ProcessorFormatter(
        foreign_pre_chain=_shared_processors,
        processors=[
            structlog.stdlib.ProcessorFormatter.remove_processors_meta,
            _renderer,
        ],
    )
)

root_logger = logging.getLogger()
# Remove any pre-existing handlers (Uvicorn, etc.)
root_logger.handlers.clear()
root_logger.addHandler(_handler)
root_logger.setLevel(_log_level)

logging.getLogger("web").setLevel(_log_level)

if _use_json:
    logging.getLogger("web").info("JSON logging enabled (stderr is not a TTY)")


def create_app() -> FastAPI:
    app = FastAPI(title="Conference Discovery")

    allowed_origins = [
        o.strip()
        for o in (os.environ.get("CORS_ORIGINS", "http://localhost:5173").split(","))
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