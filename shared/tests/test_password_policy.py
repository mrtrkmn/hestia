"""Property 15: Password policy validation.

Feature: hestia, Property 15: Password policy validation

For any string, the password validator should accept it if and only if
it has length >= 12 and contains at least one uppercase letter, one
lowercase letter, one digit, and one special character.

Validates: Requirements 9.5
"""

import string

from hypothesis import given, settings
from hypothesis import strategies as st

from shared.auth import validate_password


def _meets_policy(pw: str) -> bool:
    """Reference implementation of the password policy."""
    return (
        len(pw) >= 12
        and any(c.isupper() for c in pw)
        and any(c.islower() for c in pw)
        and any(c.isdigit() for c in pw)
        and any(c not in string.ascii_letters + string.digits for c in pw)
    )


# Strategy: printable strings of varying length (0–50)
_passwords = st.text(
    alphabet=st.characters(min_codepoint=32, max_codepoint=126),
    min_size=0,
    max_size=50,
)


@given(pw=_passwords)
@settings(max_examples=200)
def test_password_policy_matches_spec(pw: str) -> None:
    assert validate_password(pw) == _meets_policy(pw)


# Targeted: always-valid passwords
_valid_passwords = st.tuples(
    st.text(st.sampled_from(string.ascii_uppercase), min_size=1, max_size=5),
    st.text(st.sampled_from(string.ascii_lowercase), min_size=1, max_size=5),
    st.text(st.sampled_from(string.digits), min_size=1, max_size=5),
    st.text(st.sampled_from("!@#$%^&*()-_=+"), min_size=1, max_size=5),
).map(lambda parts: "".join(parts)).filter(lambda s: len(s) >= 12)


@given(pw=_valid_passwords)
@settings(max_examples=100)
def test_valid_passwords_accepted(pw: str) -> None:
    assert validate_password(pw) is True


# Targeted: too-short passwords should always fail
@given(pw=st.text(min_size=0, max_size=11))
@settings(max_examples=100)
def test_short_passwords_rejected(pw: str) -> None:
    assert validate_password(pw) is False
