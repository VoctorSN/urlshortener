from __future__ import annotations

import logging
import secrets
from dataclasses import dataclass
import jwt
from fastapi import HTTPException, Request, status
from jwt import ExpiredSignatureError, InvalidTokenError
from jwt.types import Options

from app.config import settings


logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class AuthContext:
    """Authentication context resolved from Authorization header."""

    principal: str
    auth_type: str


def _parse_bearer_token(request: Request) -> str:
    authorization = request.headers.get("Authorization")
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing Authorization header",
            headers={"WWW-Authenticate": "Bearer"},
        )

    parts = authorization.strip().split()
    if len(parts) != 2 or parts[0].lower() != "bearer":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid Authorization header format. Use Bearer <token>",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return parts[1]


def _validate_api_token(token: str) -> AuthContext | None:
    for configured_token in settings.API_TOKENS:
        if configured_token and secrets.compare_digest(token, configured_token):
            return AuthContext(principal="api-token", auth_type="api_token")
    return None


def _validate_jwt(token: str) -> AuthContext | None:
    if not settings.JWT_SECRET:
        return None

    options: Options = {"verify_aud": settings.JWT_AUDIENCE is not None}
    try:
        payload = jwt.decode(
            token,
            settings.JWT_SECRET,
            algorithms=[settings.JWT_ALGORITHM],
            audience=settings.JWT_AUDIENCE,
            options=options,
        )
    except ExpiredSignatureError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="JWT has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except InvalidTokenError as exc:
        logger.warning(
            "JWT validation failed: %s (%s)",
            exc,
            exc.__class__.__name__,
        )
        return None

    subject = str(payload.get("sub") or "jwt-user")
    return AuthContext(principal=subject, auth_type="jwt")


def _split_pattern(pattern: str) -> tuple[str | None, str]:
    value = pattern.strip()
    if " " not in value:
        return None, value

    method, path_pattern = value.split(" ", 1)
    method = method.strip().upper()
    path_pattern = path_pattern.strip()
    if not path_pattern:
        return None, value
    return method, path_pattern


def _match_path_pattern(path: str, pattern: str) -> bool:
    if pattern == path:
        return True

    if pattern.endswith("/*"):
        base = pattern[:-2]
        return path == base or path.startswith(f"{base}/")

    if pattern == "/{short_code}":
        if path.startswith("/api"):
            return False
        segment = path.strip("/")
        if not segment or "/" in segment:
            return False
        reserved = {"health", "docs", "redoc", "openapi.json", "favicon.ico"}
        return segment not in reserved

    return False


def _matches_route(method: str, path: str, pattern: str) -> bool:
    expected_method, path_pattern = _split_pattern(pattern)
    if expected_method is not None and expected_method != method.upper():
        return False
    return _match_path_pattern(path, path_pattern)


def is_exempt_route(method: str, path: str) -> bool:
    return any(
        _matches_route(method=method, path=path, pattern=pattern)
        for pattern in settings.AUTH_EXEMPT_ROUTE_PATTERNS
    )


def is_protected_route(method: str, path: str) -> bool:
    return any(
        _matches_route(method=method, path=path, pattern=pattern)
        for pattern in settings.AUTH_PROTECTED_ROUTE_PATTERNS
    )


def authenticate_request(request: Request) -> AuthContext:
    token = _parse_bearer_token(request)

    api_context = _validate_api_token(token)
    if api_context:
        return api_context

    jwt_context = _validate_jwt(token)
    if jwt_context:
        return jwt_context

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid authentication token",
        headers={"WWW-Authenticate": "Bearer"},
    )


async def enforce_token_auth(request: Request) -> AuthContext | None:
    if not settings.AUTH_ENABLED:
        return None

    method = request.method.upper()
    if method == "OPTIONS":
        return None

    path = request.url.path

    if is_exempt_route(method=method, path=path):
        return None

    if not is_protected_route(method=method, path=path):
        return None

    return authenticate_request(request)
