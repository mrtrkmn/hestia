"""TOTP validation module for Hestia.

Generates TOTP secrets and validates codes for the current
and adjacent time windows.

Requirement 9.2
"""

from __future__ import annotations

import pyotp


def generate_totp_secret() -> str:
    """Generate a new random TOTP secret (base32-encoded).

    Returns
    -------
    str
        A base32-encoded secret suitable for provisioning into
        an authenticator app.
    """
    return pyotp.random_base32()


def validate_totp(secret: str, code: str) -> bool:
    """Return *True* iff *code* is valid for the TOTP *secret*.

    Accepts the current time window and ±1 adjacent windows
    (``valid_window=1``).
    """
    totp = pyotp.TOTP(secret)
    return totp.verify(code, valid_window=1)
