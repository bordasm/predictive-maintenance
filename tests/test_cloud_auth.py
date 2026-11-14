from __future__ import annotations

import base64
import json

from fastapi import Depends, FastAPI
from fastapi.testclient import TestClient

from predictive_maintenance.serving.authentication import (
    AuthenticatedUser,
    build_identity_guard,
)


def test_firebase_guard_accepts_gateway_forwarded_token() -> None:
    def verify(token: str) -> dict[str, str]:
        if token != "valid-token":
            raise ValueError("invalid token")
        return {"uid": "user-123", "email": "operator@example.com"}

    guard = build_identity_guard("demo-project", token_verifier=verify)
    app = FastAPI()

    @app.get("/protected")
    def protected(user: AuthenticatedUser = Depends(guard)) -> dict[str, str | None]:
        return {"uid": user.uid, "email": user.email}

    with TestClient(app) as client:
        missing = client.get("/protected")
        direct = client.get(
            "/protected", headers={"Authorization": "Bearer valid-token"}
        )
        forwarded = client.get(
            "/protected",
            headers={"X-Forwarded-Authorization": "Bearer valid-token"},
        )
        invalid = client.get(
            "/protected", headers={"Authorization": "Bearer invalid"}
        )

    assert missing.status_code == 401
    assert direct.json() == {"uid": "user-123", "email": "operator@example.com"}
    assert forwarded.status_code == 200
    assert invalid.status_code == 401


def test_firebase_guard_prefers_user_token_forwarded_by_gateway() -> None:
    verified_tokens: list[str] = []

    def verify(token: str) -> dict[str, str]:
        verified_tokens.append(token)
        if token != "firebase-user-token":
            raise ValueError("invalid token")
        return {"uid": "user-123", "email": "operator@example.com"}

    guard = build_identity_guard("demo-project", token_verifier=verify)
    app = FastAPI()

    @app.get("/protected")
    def protected(user: AuthenticatedUser = Depends(guard)) -> dict[str, str | None]:
        return {"uid": user.uid, "email": user.email}

    with TestClient(app) as client:
        response = client.get(
            "/protected",
            headers={
                "Authorization": "Bearer cloud-run-backend-token",
                "X-Forwarded-Authorization": "Bearer firebase-user-token",
            },
        )

    assert response.status_code == 200
    assert response.json() == {"uid": "user-123", "email": "operator@example.com"}
    assert verified_tokens == ["firebase-user-token"]


def test_firebase_guard_accepts_authenticated_gateway_userinfo() -> None:
    def verify(_token: str) -> dict[str, str]:
        raise AssertionError("Gateway-authenticated claims must not be reverified")

    claims = {
        "iss": "https://securetoken.google.com/demo-project",
        "aud": "demo-project",
        "sub": "user-123",
        "email": "operator@example.com",
    }
    userinfo = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    guard = build_identity_guard("demo-project", token_verifier=verify)
    app = FastAPI()

    @app.get("/protected")
    def protected(user: AuthenticatedUser = Depends(guard)) -> dict[str, str | None]:
        return {"uid": user.uid, "email": user.email}

    with TestClient(app) as client:
        response = client.get(
            "/protected",
            headers={
                "Authorization": "Bearer cloud-run-backend-token",
                "X-Apigateway-Api-Userinfo": userinfo,
            },
        )

    assert response.status_code == 200
    assert response.json() == {"uid": "user-123", "email": "operator@example.com"}


def test_firebase_guard_rejects_gateway_userinfo_for_another_project() -> None:
    claims = {
        "iss": "https://securetoken.google.com/other-project",
        "aud": "other-project",
        "sub": "user-123",
    }
    userinfo = base64.urlsafe_b64encode(json.dumps(claims).encode()).decode().rstrip("=")
    guard = build_identity_guard(
        "demo-project", token_verifier=lambda _token: {"uid": "unexpected"}
    )
    app = FastAPI()

    @app.get("/protected")
    def protected(user: AuthenticatedUser = Depends(guard)) -> dict[str, str]:
        return {"uid": user.uid}

    with TestClient(app) as client:
        response = client.get(
            "/protected", headers={"X-Apigateway-Api-Userinfo": userinfo}
        )

    assert response.status_code == 401
    assert response.json()["detail"] == "The API Gateway identity is invalid"


def test_identity_guard_preserves_local_anonymous_mode() -> None:
    guard = build_identity_guard(None)
    user = guard()
    assert user == AuthenticatedUser(uid="local-anonymous", email=None)
