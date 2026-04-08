"""Input validation, sanitization, and rate limiting middleware.

Requirements: 15.7, 15.8, 17.3
"""

from __future__ import annotations

import re
import time
from collections import defaultdict

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse, Response

# --- Sanitization patterns ---
_SQL_INJECTION = re.compile(
    r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|UNION|ALTER|CREATE|EXEC)\b\s*)"
    r"|(\bOR\b\s+\S+\s*=)",
    re.IGNORECASE,
)
_PATH_TRAVERSAL = re.compile(r"\.\.[/\\]+")
_XSS_SCRIPT = re.compile(r"<\s*script[^>]*>", re.IGNORECASE)
_XSS_EVENT = re.compile(r"\bon\w+\s*=", re.IGNORECASE)


def sanitize(value: str) -> str:
    """Neutralize dangerous patterns in user input (applied repeatedly until stable)."""
    for _ in range(10):
        prev = value
        value = _PATH_TRAVERSAL.sub("", value)
        value = _XSS_SCRIPT.sub("", value)
        value = _XSS_EVENT.sub("", value)
        value = _SQL_INJECTION.sub("", value)
        if value == prev:
            break
    return value


def is_dangerous(value: str) -> bool:
    """Return True if value contains dangerous patterns."""
    return bool(
        _SQL_INJECTION.search(value)
        or _PATH_TRAVERSAL.search(value)
        or _XSS_SCRIPT.search(value)
        or _XSS_EVENT.search(value)
    )


class SanitizationMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        for key, val in request.query_params.items():
            if is_dangerous(val):
                return JSONResponse(
                    status_code=400,
                    content={"error": "validation_error", "message": "Potentially dangerous input detected", "field": key},
                )
        return await call_next(request)


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Per-user rate limiting. Default 100 req/min."""

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 60) -> None:  # type: ignore[no-untyped-def]
        super().__init__(app)
        self.max_requests = max_requests
        self.window = window_seconds
        self._buckets: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        user_id = getattr(request.state, "user_id", None) or request.client.host  # type: ignore[union-attr]
        now = time.time()
        bucket = self._buckets[user_id]
        cutoff = now - self.window
        self._buckets[user_id] = [t for t in bucket if t > cutoff]
        bucket = self._buckets[user_id]

        if len(bucket) >= self.max_requests:
            return JSONResponse(
                status_code=429,
                content={"detail": "Rate limit exceeded"},
                headers={"Retry-After": str(self.window)},
            )
        bucket.append(now)
        return await call_next(request)
