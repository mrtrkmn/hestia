"""Property tests for the API Gateway.

Property 14: Missing or invalid JWT returns 401
Property 26: Input sanitization
Property 28: API validation error response
Property 29: API endpoint versioning

Validates: Requirements 9.4, 15.7, 17.3, 17.4
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

import pytest
from httpx import ASGITransport, AsyncClient
from hypothesis import given, settings
from hypothesis import strategies as st

from app.main import app
from shared.auth import issue_jwt
from app.middleware.validation import sanitize, is_dangerous

_SECRET = "change-me-in-production"  # matches default in shared config


def _reset_rate_limiter():
    """Clear rate limiter state between tests."""
    for mw in app.user_middleware:
        if hasattr(mw, "kwargs") and "max_requests" in (mw.kwargs or {}):
            pass
    # Walk the middleware stack to find the RateLimitMiddleware
    from app.middleware.validation import RateLimitMiddleware
    stack = app.middleware_stack
    while stack is not None:
        if isinstance(stack, RateLimitMiddleware):
            stack._buckets.clear()
            break
        stack = getattr(stack, "app", None)


@pytest.fixture(autouse=True)
def reset_rate_limit():
    _reset_rate_limiter()
    yield
    _reset_rate_limiter()


# ---------------------------------------------------------------------------
# Property 14: Missing or invalid JWT returns 401
# Feature: hestia, Property 14: Missing or invalid JWT returns 401
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_missing_token_returns_401():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/v1/jobs")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_garbage_token_returns_401():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/v1/jobs", headers={"Authorization": "Bearer garbage.token.here"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_expired_token_returns_401():
    token = issue_jwt("user1", "user", _SECRET, expires_in=-1)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/v1/jobs", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_tampered_token_returns_401():
    token = issue_jwt("user1", "user", _SECRET)
    tampered = token[:-4] + "XXXX"
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/v1/jobs", headers={"Authorization": f"Bearer {tampered}"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_wrong_secret_returns_401():
    token = issue_jwt("user1", "user", "wrong-secret-key-value-here!!")
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/v1/jobs", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


# ASCII-only tokens to avoid httpx encoding issues
@given(token=st.text(
    alphabet=st.characters(min_codepoint=32, max_codepoint=126),
    min_size=1, max_size=200,
))
@settings(max_examples=100)
@pytest.mark.asyncio
async def test_property_random_tokens_return_401(token: str):
    """Property 14: random ASCII strings as tokens should yield 401."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.get("/api/v1/jobs", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Property 26: Input sanitization
# Feature: hestia, Property 26: Input sanitization
# ---------------------------------------------------------------------------

_SQL_PAYLOADS = st.sampled_from([
    "'; DROP TABLE users; --",
    "UNION SELECT * FROM passwords",
    "'; DELETE FROM jobs; --",
])

_XSS_PAYLOADS = st.sampled_from([
    '<script>alert("xss")</script>',
    '<img onerror="alert(1)" src=x>',
    '<div onmouseover="steal()">',
])

_PATH_TRAVERSAL_PAYLOADS = st.sampled_from([
    "../../../etc/passwd",
    "..\\..\\windows\\system32",
])


@given(payload=_SQL_PAYLOADS)
@settings(max_examples=50)
def test_sql_injection_detected(payload: str):
    assert is_dangerous(payload)
    cleaned = sanitize(payload)
    assert not is_dangerous(cleaned)


@given(payload=_XSS_PAYLOADS)
@settings(max_examples=50)
def test_xss_detected(payload: str):
    assert is_dangerous(payload)
    cleaned = sanitize(payload)
    assert not is_dangerous(cleaned)


@given(payload=_PATH_TRAVERSAL_PAYLOADS)
@settings(max_examples=50)
def test_path_traversal_detected(payload: str):
    assert is_dangerous(payload)
    cleaned = sanitize(payload)
    assert not is_dangerous(cleaned)


# ---------------------------------------------------------------------------
# Property 28: API validation error response
# Feature: hestia, Property 28: API validation error response
# ---------------------------------------------------------------------------

@pytest.mark.asyncio
async def test_missing_required_field_returns_422():
    token = issue_jwt("user1", "user", _SECRET)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post(
            "/api/v1/files/process",
            json={},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 422
    body = r.json()
    assert "detail" in body


@pytest.mark.asyncio
async def test_invalid_field_type_returns_422():
    token = issue_jwt("user1", "user", _SECRET)
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
        r = await c.post(
            "/api/v1/pipelines",
            json={"name": 123, "steps": "not-a-list"},
            headers={"Authorization": f"Bearer {token}"},
        )
    assert r.status_code == 422
    body = r.json()
    assert "detail" in body


# ---------------------------------------------------------------------------
# Property 29: API endpoint versioning
# Feature: hestia, Property 29: API endpoint versioning
# ---------------------------------------------------------------------------

_INFRA_PATHS = {"/openapi.json", "/api/docs", "/docs/oauth2-redirect", "/redoc", "/healthz"}


def test_all_api_routes_versioned():
    """Every non-infrastructure route must start with /api/v1/."""
    for route in app.routes:
        path = getattr(route, "path", "")
        if path in _INFRA_PATHS or not path:
            continue
        assert path.startswith("/api/v1/"), f"Route {path} is not versioned under /api/v1/"
