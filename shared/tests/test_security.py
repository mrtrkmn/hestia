"""Property tests for security defaults.

Property 25: Secret generation uniqueness and entropy
Property 27: Security event structured logging

Validates: Requirements 15.2, 7.5, 15.9
"""

import json
from hypothesis import given, settings
from hypothesis import strategies as st

from shared.security import generate_secret, generate_deployment_secrets, log_security_event


# ---------------------------------------------------------------------------
# Property 25: Secret generation uniqueness and entropy
# Feature: hestia, Property 25: Secret generation uniqueness and entropy
# ---------------------------------------------------------------------------

@given(n=st.integers(min_value=2, max_value=20))
@settings(max_examples=50)
def test_secrets_are_unique(n: int):
    secrets_set = {generate_secret() for _ in range(n)}
    assert len(secrets_set) == n


def test_deployment_secrets_unique_and_sufficient_entropy():
    s = generate_deployment_secrets()
    values = list(s.values())
    # All unique
    assert len(set(values)) == len(values)
    # Each has >= 256 bits of entropy (32 bytes = 64 hex chars)
    for v in values:
        assert len(v) >= 64


# ---------------------------------------------------------------------------
# Property 27: Security event structured logging
# Feature: hestia, Property 27: Security event structured logging
# ---------------------------------------------------------------------------

_event_types = st.sampled_from(["auth_failure", "permission_denied", "config_change", "vpn_auth_failure"])
_ips = st.from_regex(r"\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}", fullmatch=True)
_users = st.text(min_size=1, max_size=20)
_resources = st.text(min_size=1, max_size=50)


@given(event_type=_event_types, ip=_ips, user=_users, resource=_resources)
@settings(max_examples=100)
def test_security_log_has_required_fields(event_type: str, ip: str, user: str, resource: str):
    line = log_security_event(event_type, ip, user=user, resource=resource, details="test")
    entry = json.loads(line)
    assert entry["event_type"] == event_type
    assert entry["timestamp"]
    assert entry["source_ip"] == ip
    assert entry["user"] == user
    assert entry["resource"] == resource
