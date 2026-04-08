"""Property 13: JWT issue-then-verify round-trip.

Feature: hestia, Property 13: JWT issue-then-verify round-trip

For any valid user authentication, the issued JWT should be verifiable
with the signing key, contain the correct user_id and role, and have
an expiration matching the configured duration.

Validates: Requirements 9.3
"""

import time

from hypothesis import given, settings
from hypothesis import strategies as st

from shared.auth import issue_jwt, verify_jwt

_user_ids = st.text(
    alphabet=st.characters(min_codepoint=48, max_codepoint=122),
    min_size=1,
    max_size=30,
)
_roles = st.sampled_from(["admin", "user"])
_secrets = st.text(min_size=8, max_size=64)
_expires = st.integers(min_value=60, max_value=86400)


@given(user_id=_user_ids, role=_roles, secret=_secrets, expires_in=_expires)
@settings(max_examples=200)
def test_jwt_roundtrip(user_id: str, role: str, secret: str, expires_in: int) -> None:
    token = issue_jwt(user_id, role, secret, expires_in=expires_in)
    claims = verify_jwt(token, secret)

    assert claims["user_id"] == user_id
    assert claims["role"] == role
    # exp should be within a small window of now + expires_in
    assert abs(claims["exp"] - (int(time.time()) + expires_in)) <= 2
