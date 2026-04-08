"""Property 16: RBAC authorization enforcement.

Feature: hestia, Property 16: RBAC authorization enforcement

For any user with a given role and any API endpoint, access should be
granted if and only if the user's role has permission for that endpoint.
Admin-only endpoints should reject users with the "user" role.

Validates: Requirements 9.7
"""

from hypothesis import given, settings
from hypothesis import strategies as st

from shared.auth import check_rbac

_methods = st.sampled_from(["GET", "POST", "PUT", "DELETE"])

_admin_endpoints = st.from_regex(r"/api/v1/admin(/[a-z]+)*", fullmatch=True)
_user_endpoints = st.sampled_from([
    "/api/v1/files/process",
    "/api/v1/jobs",
    "/api/v1/jobs/123",
    "/api/v1/pipelines",
    "/api/v1/storage/shares",
    "/api/v1/iot/automations",
    "/api/v1/services/health",
    "/api/docs",
])


@given(endpoint=_admin_endpoints, method=_methods)
@settings(max_examples=100)
def test_admin_endpoints_allow_admin(endpoint: str, method: str) -> None:
    assert check_rbac("admin", endpoint, method) is True


@given(endpoint=_admin_endpoints, method=_methods)
@settings(max_examples=100)
def test_admin_endpoints_deny_user(endpoint: str, method: str) -> None:
    assert check_rbac("user", endpoint, method) is False


@given(endpoint=_user_endpoints, method=_methods)
@settings(max_examples=100)
def test_user_endpoints_allow_both_roles(endpoint: str, method: str) -> None:
    assert check_rbac("admin", endpoint, method) is True
    assert check_rbac("user", endpoint, method) is True


@given(
    role=st.text(min_size=1, max_size=10).filter(lambda r: r not in ("admin", "user")),
    endpoint=_user_endpoints,
    method=_methods,
)
@settings(max_examples=100)
def test_unknown_roles_denied(role: str, endpoint: str, method: str) -> None:
    assert check_rbac(role, endpoint, method) is False
