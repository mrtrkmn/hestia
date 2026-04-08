"""RBAC (Role-Based Access Control) module for Hestia.

Defines admin-only and user-accessible endpoints and checks whether
a user role has permission for a given endpoint.

Requirement 9.7
"""

from __future__ import annotations

import re

from shared.models.auth import UserRole

# Admin-only endpoint pattern — everything under /api/v1/admin/*
_ADMIN_PATTERN = re.compile(r"^/api/v1/admin(/.*)?$")

# Endpoints accessible to each role
ADMIN_ONLY_PREFIXES: list[str] = [
    "/api/v1/admin",
]

USER_ACCESSIBLE_PREFIXES: list[str] = [
    "/api/v1/files",
    "/api/v1/jobs",
    "/api/v1/pipelines",
    "/api/v1/storage",
    "/api/v1/iot",
    "/api/v1/services/health",
    "/api/docs",
]


def check_rbac(role: str | UserRole, endpoint: str, method: str = "GET") -> bool:
    """Return *True* iff *role* is authorised for *endpoint*.

    Rules
    -----
    * ``admin`` role has access to **all** endpoints.
    * ``user`` role is denied any endpoint matching ``/api/v1/admin/*``.
    * Any unrecognised role is denied access to everything (zero-trust).
    """
    role_value = role.value if isinstance(role, UserRole) else role

    if role_value == UserRole.ADMIN.value:
        return True
    if role_value == UserRole.USER.value:
        return not _ADMIN_PATTERN.match(endpoint)
    # Unknown roles are denied by default.
    return False
