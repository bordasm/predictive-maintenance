"""Serve the browser dashboard and its non-secret runtime configuration."""

from __future__ import annotations

import json
import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles


STATIC_DIR = Path(__file__).with_name("static")


def create_web_app() -> FastAPI:
    application = FastAPI(
        title="Predictive Maintenance Demo",
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    application.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

    @application.get("/health", include_in_schema=False)
    def health() -> dict[str, str]:
        return {"status": "ready"}

    @application.get("/config.js", include_in_schema=False)
    def runtime_config() -> Response:
        config = {
            "apiBaseUrl": os.environ.get("PREDMAINT_API_URL", "http://localhost:8000"),
            "firebaseApiKey": os.environ.get("PREDMAINT_FIREBASE_API_KEY", ""),
            "firebaseProjectId": os.environ.get("PREDMAINT_FIREBASE_PROJECT_ID", ""),
        }
        return Response(
            content=f"window.PREDMAINT_CONFIG = {json.dumps(config)};\n",
            media_type="application/javascript",
            headers={"Cache-Control": "no-store"},
        )

    @application.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    return application


app = create_web_app()
