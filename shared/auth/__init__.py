"""Authentication and authorization package for Hestia.

Provides password validation, JWT issue/verify, TOTP validation,
and RBAC enforcement that complement the Authelia SSO layer.

Requirements: 9.1, 9.2, 9.3, 9.5, 9.6, 9.7
"""

from shared.auth.jwt_validator import issue_jwt, verify_jwt as _verify_jwt, JWTClaims
from shared.auth.password_policy import validate_password as _validate_password_detailed
from shared.auth.totp import generate_totp_secret, validate_totp
from shared.auth.rbac import check_rbac
from shared.auth.mqtt_credentials import MQTTCredentialStore


def validate_password(password: str) -> bool:
    """Return *True* iff *password* satisfies the Hub password policy.

    Policy: length >= 12, at least one uppercase, lowercase, digit, special.
    """
    ok, _ = _validate_password_detailed(password)
    return ok


def verify_jwt(token: str, secret: str) -> dict:
    """Validate *token* and return claims as a plain dict.

    Returns a dict with keys ``user_id``, ``role``, and ``exp``.

    Raises jwt.ExpiredSignatureError / jwt.InvalidTokenError on failure.
    """
    claims: JWTClaims = _verify_jwt(token, secret)
    return {
        "user_id": claims.user_id,
        "role": claims.role,
        "exp": claims.exp,
    }


__all__ = [
    "issue_jwt",
    "verify_jwt",
    "validate_password",
    "generate_totp_secret",
    "validate_totp",
    "check_rbac",
    "MQTTCredentialStore",
]
