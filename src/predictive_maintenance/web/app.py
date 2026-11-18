"""Serve the browser dashboard and its non-secret runtime configuration."""

from __future__ import annotations

import json
import logging
import os
import re
from pathlib import Path
from typing import Literal

from fastapi import FastAPI, HTTPException, Request
from fastapi.concurrency import run_in_threadpool
from fastapi.responses import FileResponse, Response
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field, field_validator

from predictive_maintenance.web.access_requests import (
    AccessRequestRateLimited,
    AccessRequestService,
)


STATIC_DIR = Path(__file__).with_name("static")
EMAIL_PATTERN = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")
LOGGER = logging.getLogger(__name__)


class AccessRequestPayload(BaseModel):
    email: str = Field(min_length=3, max_length=100)
    message: str = Field(min_length=1, max_length=1000)
    locale: Literal["en", "hu"] = "en"
    website: str = Field(default="", max_length=200)

    @field_validator("email")
    @classmethod
    def validate_email(cls, value: str) -> str:
        normalized = value.strip().lower()
        if not EMAIL_PATTERN.fullmatch(normalized):
            raise ValueError("invalid email address")
        return normalized

    @field_validator("message")
    @classmethod
    def validate_message(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("message is required")
        return normalized


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

    @application.post("/access-requests", status_code=202, include_in_schema=False)
    async def access_request(payload: AccessRequestPayload, request: Request) -> dict[str, str]:
        # A hidden honeypot field absorbs basic form bots without confirming detection.
        if payload.website:
            return {"status": "accepted"}
        forwarded_for = request.headers.get("x-forwarded-for", "")
        client_ip = forwarded_for.split(",", 1)[0].strip()
        if not client_ip and request.client:
            client_ip = request.client.host
        try:
            service = getattr(application.state, "access_request_service", None)
            if service is None:
                service = AccessRequestService()
            result = await run_in_threadpool(
                service.submit,
                email=payload.email,
                message=payload.message,
                locale=payload.locale,
                client_ip=client_ip,
            )
        except AccessRequestRateLimited:
            raise HTTPException(status_code=429, detail="request limit exceeded") from None
        except Exception:
            LOGGER.exception("Access request submission failed")
            raise HTTPException(status_code=503, detail="access request service unavailable") from None
        return {
            "status": "accepted",
            "notification": "sent" if result.notification_sent else "pending",
        }

    @application.get("/", include_in_schema=False)
    def index() -> FileResponse:
        return FileResponse(STATIC_DIR / "index.html")

    return application


app = create_web_app()
