"""Authentication dependencies for local and Google Cloud deployments."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Annotated, Any, Callable

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader, HTTPAuthorizationCredentials, HTTPBearer


@dataclass(frozen=True)
class AuthenticatedUser:
    """Identity attached to an authenticated inference request."""

    uid: str
    email: str | None = None


TokenVerifier = Callable[[str], dict[str, Any]]

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)
BEARER_TOKEN = HTTPBearer(auto_error=False)
FORWARDED_AUTHORIZATION = APIKeyHeader(
    name="X-Forwarded-Authorization", auto_error=False
)


def _firebase_verifier(project_id: str) -> TokenVerifier:
    """Build a lazy Firebase verifier backed by application default credentials."""

    def verify(token: str) -> dict[str, Any]:
        import firebase_admin
        from firebase_admin import auth

        try:
            firebase_admin.get_app()
        except ValueError:
            firebase_admin.initialize_app(options={"projectId": project_id})
        return auth.verify_id_token(token, check_revoked=True)

    return verify


def build_identity_guard(
    firebase_project_id: str | None,
    legacy_api_key: str | None = None,
    token_verifier: TokenVerifier | None = None,
) -> Callable[..., AuthenticatedUser]:
    """Return the configured authentication dependency.

    Cloud deployments use Firebase ID tokens. The API-key mode remains available
    for local backwards compatibility, and an entirely unconfigured local app is
    intentionally anonymous.
    """

    verifier = (
        token_verifier
        if token_verifier is not None
        else _firebase_verifier(firebase_project_id)
        if firebase_project_id
        else None
    )

    def require_identity(
        bearer: Annotated[
            HTTPAuthorizationCredentials | None, Security(BEARER_TOKEN)
        ] = None,
        forwarded_authorization: Annotated[
            str | None, Security(FORWARDED_AUTHORIZATION)
        ] = None,
        supplied_api_key: Annotated[
            str | None, Security(API_KEY_HEADER)
        ] = None,
    ) -> AuthenticatedUser:
        if verifier is not None:
            token = None
            if forwarded_authorization:
                scheme, _, value = forwarded_authorization.partition(" ")
                if scheme.lower() == "bearer" and value:
                    token = value
            if token is None and bearer is not None:
                token = bearer.credentials
            if token is None:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="A Firebase ID token is required",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            try:
                claims = verifier(token)
            except Exception as error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="The Firebase ID token is invalid or expired",
                    headers={"WWW-Authenticate": "Bearer"},
                ) from error
            uid = str(claims.get("uid") or claims.get("sub") or "")
            if not uid:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="The Firebase ID token has no subject",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            email = claims.get("email")
            return AuthenticatedUser(uid=uid, email=str(email) if email else None)

        if legacy_api_key:
            import secrets

            if supplied_api_key is None or not secrets.compare_digest(
                supplied_api_key, legacy_api_key
            ):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="A valid API key is required",
                    headers={"WWW-Authenticate": "ApiKey"},
                )
            return AuthenticatedUser(uid="legacy-api-key")

        return AuthenticatedUser(uid="local-anonymous")

    return require_identity
