"""Authentication and authorization utilities for Hestia.

Provides password validation, JWT issue/verify, TOTP validation,
and RBAC enforcement that complement the Authelia SSO layer.

Requirements: 9.1, 9.2, 9.3, 9.5, 9.6, 9.7
"""

from __future__ import annotations

import re
import time
from datetime import datetime, timezone

import jwt
import pyotp


# ---------------------------------------------------------------------------
# Password policy  (Requirement 9.5)
# Min 12 chars, at least one upper, lower, digit, special character
# ---------------------------------------------------------------------------

_UPPER_RE = re.compile(r"[A-Z]")
_LOWER_RE = re.compile(r"[a-z]")
_DIGIT_RE = re.compile(r"[0-9]")
_SPECIAL_RE = re.compile(r"[^A-Za-z0-9]")


def validate_password(password: str) -> bool:
    """Return *True* iff *password* satisfies the Hub password policy.

    Policy:
    - length >= 12
    - at least one uppercase letter
    - at least one lowercase letter
    - at least one digit
    - at least one special (non-alphanumeric) character
    """
    if len(password) < 12:
        return False
    if not _UPPER_RE.search(password):
        return False
    if not _LOWER_RE.search(password):
        return False
    if not _DIGIT_RE.search(password):
        return False
    if not _SPECIAL_RE.search(password):
        return False
    return True


# ---------------------------------------------------------------------------
# JWT helpers  (Requirement 9.3)
# ---------------------------------------------------------------------------

_JWT_ALGORITHM = "HS256"


def issue_jwt(
    user_id: str,
    role: str,
    secret: str,
    expires_in: int = 3600,
) -> str:
    """Create a signed JWT containing *user_id* and *role* claims.

    Parameters
    ----------
    user_id:
        Unique identifier for the authenticated user.
    role:
        User role (e.g. ``"admin"`` or ``"user"``).
    secret:
        HMAC secret used to sign the token.
    expires_in:
        Token lifetime in seconds (default 1 hour).

    Returns
    -------
    str
        Encoded JWT string.
    """
    now = int(time.time())
    payload = {
        "sub": user_id,
        "role": role,
        "iat": now,
        "exp": now + expires_in,
    }
    return jwt.encode(payload, secret, algorithm=_JWT_ALGORITHM)


def verify_jwt(token: str, secret: str) -> dict:
    """Validate *token* and return its claims.

    Returns a dict with keys ``user_id``, ``role``, and ``exp``.

    Raises
    ------
    jwt.ExpiredSignatureError
        If the token has expired.
    jwt.InvalidTokenError
        If the token is malformed or the signature is invalid.
    """
    payload = jwt.decode(token, secret, algorithms=[_JWT_ALGORITHM])
    return {
        "user_id": payload["sub"],
        "role": payload["role"],
        "exp": payload["exp"],
    }


# ---------------------------------------------------------------------------
# TOTP helpers  (Requirement 9.2)
# ---------------------------------------------------------------------------


def validate_totp(secret: str, code: str) -> bool:
    """Return *True* iff *code* is valid for the TOTP *secret*.

    Accepts the current time window and ±1 adjacent windows (``valid_window=1``).
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)


# ---------------------------------------------------------------------------
# RBAC helpers  (Requirement 9.7)
# ---------------------------------------------------------------------------

# Admin-only endpoint patterns.  Everything under /api/v1/admin/* is
# restricted to the ``admin`` role.  All other endpoints are accessible
# to both ``admin`` and ``user`` roles.
_ADMIN_PATTERN = re.compile(r"^/api/v1/admin(/.*)?$")


def check_rbac(role: str, endpoint: str, method: str) -> bool:
    """Return *True* iff *role* is authorised for *endpoint* + *method*.

    Rules
    -----
    * ``admin`` role has access to **all** endpoints.
    * ``user`` role is denied any endpoint matching ``/api/v1/admin/*``.
    * Any unrecognised role is denied access to everything.
    """
    if role == "admin":
        return True
    if role == "user":
        return not _ADMIN_PATTERN.match(endpoint)
    # Unknown roles are denied by default (zero-trust).
    return False
