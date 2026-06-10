import logging
import os
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from web.api import router as api_router
from web.api.pipeline import router as pipeline_router
from web.api.discovery import router as discovery_router

_log_level = logging.DEBUG if "--debug" in sys.argv else logging.INFO
logging.basicConfig(
    level=_log_level,
    format="%(asctime)s %(levelname)-8s %(name)s %(message)s",
    datefmt="%H:%M:%S",
    stream=sys.stdout,
)
logging.getLogger("web").setLevel(_log_level)


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