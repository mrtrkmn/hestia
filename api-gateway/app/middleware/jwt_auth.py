"""JWT authentication middleware.

Validates JWT tokens on incoming requests. Returns HTTP 401 for
missing, expired, or tampered tokens.

Requirements: 9.4
"""

from __future__ import annotations

import re

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

from shared.auth import verify_jwt


# Paths that don't require authentication
_PUBLIC_PATHS = re.compile(
    r"^(/auth/|/api/docs|/openapi\.json|/healthz)"
)


class JWTMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, secret: str, login_url: str = "/auth/login") -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.secret = secret
        self.login_url = login_url

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        if _PUBLIC_PATHS.match(request.url.path):
            return await call_next(request)

        auth_header = request.headers.get("Authorization")
        if not auth_header or not auth_header.startswith("Bearer "):
            return JSONResponse(
                status_code=401,
                content={"detail": "Missing or invalid Authorization header"},
            )

        token = auth_header[7:]
        try:
            claims = verify_jwt(token, self.secret)
        except Exception:
            return JSONResponse(
                status_code=401,
                content={"detail": "Invalid or expired token"},
            )

        request.state.user_id = claims["user_id"]
        request.state.role = claims["role"]
        return await call_next(request)
