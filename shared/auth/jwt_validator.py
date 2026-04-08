"""JWT validation module for Hestia.

Validates JWT tokens issued by Authelia, extracts user_id and role claims,
and returns structured errors for invalid/expired/tampered tokens.

Requirement 9.3: Issue signed JWT with configurable expiration.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

import jwt

_JWT_ALGORITHM = "HS256"


@dataclass
class JWTClaims:
    """Structured representation of validated JWT claims."""

    user_id: str
    role: str
    exp: int


class JWTError(Exception):
    """Base error for JWT validation failures."""

    def __init__(self, reason: str) -> None:
        self.reason = reason
        super().__init__(reason)


class JWTExpiredError(JWTError):
    """Raised when a JWT token has expired."""

    def __init__(self) -> None:
        super().__init__("Token has expired")


class JWTInvalidError(JWTError):
    """Raised when a JWT token is malformed or tampered with."""

    def __init__(self, detail: str = "Invalid token") -> None:
        super().__init__(detail)


class JWTMissingClaimError(JWTError):
    """Raised when a required claim is missing from the JWT."""

    def __init__(self, claim: str) -> None:
        super().__init__(f"Missing required claim: {claim}")


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


def verify_jwt(token: str, secret: str) -> JWTClaims:
    """Validate *token* and return structured claims.

    Returns
    -------
    JWTClaims
        Dataclass with ``user_id``, ``role``, and ``exp`` fields.

    Raises
    ------
    JWTExpiredError
        If the token has expired.
    JWTInvalidError
        If the token is malformed or the signature is invalid.
    JWTMissingClaimError
        If a required claim (``sub`` or ``role``) is absent.
    """
    try:
        payload = jwt.decode(token, secret, algorithms=[_JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise JWTExpiredError()
    except jwt.InvalidTokenError as exc:
        raise JWTInvalidError(str(exc))

    if "sub" not in payload:
        raise JWTMissingClaimError("sub")
    if "role" not in payload:
        raise JWTMissingClaimError("role")

    return JWTClaims(
        user_id=payload["sub"],
        role=payload["role"],
        exp=payload["exp"],
    )
