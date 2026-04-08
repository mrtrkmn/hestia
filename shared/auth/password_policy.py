"""Password policy validator for Hestia.

Validates passwords against the Hub policy:
- Minimum 12 characters
- At least one uppercase letter
- At least one lowercase letter
- At least one digit
- At least one special (non-alphanumeric) character

Requirement 9.5
"""

from __future__ import annotations

import re

_UPPER_RE = re.compile(r"[A-Z]")
_LOWER_RE = re.compile(r"[a-z]")
_DIGIT_RE = re.compile(r"[0-9]")
_SPECIAL_RE = re.compile(r"[^A-Za-z0-9]")


def validate_password(password: str) -> tuple[bool, str | None]:
    """Check whether *password* satisfies the Hub password policy.

    Returns
    -------
    tuple[bool, str | None]
        ``(True, None)`` when the password is valid, or
        ``(False, reason)`` with a human-readable explanation on failure.
    """
    if len(password) < 12:
        return False, "Password must be at least 12 characters long"
    if not _UPPER_RE.search(password):
        return False, "Password must contain at least one uppercase letter"
    if not _LOWER_RE.search(password):
        return False, "Password must contain at least one lowercase letter"
    if not _DIGIT_RE.search(password):
        return False, "Password must contain at least one digit"
    if not _SPECIAL_RE.search(password):
        return False, "Password must contain at least one special character"
    return True, None
