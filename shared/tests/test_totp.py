"""Property 12: TOTP validation correctness.

Feature: hestia, Property 12: TOTP validation correctness

For any valid TOTP secret, generating a code for the current time window
and then verifying it should succeed. Verifying any code that does not
match the current or adjacent time windows should fail.

Validates: Requirements 9.2
"""

import pyotp
from hypothesis import given, settings, assume
from hypothesis import strategies as st

from shared.auth import generate_totp_secret, validate_totp


@given(data=st.data())
@settings(max_examples=100)
def test_current_code_accepted(data: st.DataObject) -> None:
    secret = generate_totp_secret()
    totp = pyotp.TOTP(secret)
    code = totp.now()
    assert validate_totp(secret, code) is True


@given(code=st.from_regex(r"[0-9]{6}", fullmatch=True))
@settings(max_examples=100)
def test_random_code_rejected(code: str) -> None:
    """A random 6-digit code should almost certainly not match a fresh secret."""
    secret = generate_totp_secret()
    totp = pyotp.TOTP(secret)
    current = totp.now()
    # Skip if the random code happens to match the current window
    assume(code != current)
    # Also skip adjacent windows
    import time as _time
    t = int(_time.time())
    assume(code != totp.at(t - 30))
    assume(code != totp.at(t + 30))
    assert validate_totp(secret, code) is False
