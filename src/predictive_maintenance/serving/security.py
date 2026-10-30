"""Authentication and request-metadata helpers for the inference API."""

from __future__ import annotations

import re
import secrets
from collections.abc import Callable
from typing import Annotated

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
REQUEST_ID_PATTERN = re.compile(r"^[A-Za-z0-9._-]{1,64}$")


def build_api_key_guard(expected_api_key: str | None) -> Callable[..., None]:
    """Return a FastAPI dependency using constant-time secret comparison."""

    def require_api_key(
        supplied_api_key: Annotated[str | None, Security(API_KEY_HEADER)] = None,
    ) -> None:
        if not expected_api_key:
            return
        if supplied_api_key is None or not secrets.compare_digest(
            supplied_api_key, expected_api_key
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="A valid API key is required",
                headers={"WWW-Authenticate": "ApiKey"},
            )

    return require_api_key


def valid_request_id(value: str | None) -> bool:
    return value is not None and REQUEST_ID_PATTERN.fullmatch(value) is not None
