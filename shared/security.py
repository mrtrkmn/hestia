"""Secret generation and structured security logging.

Requirements: 15.2, 15.9, 7.5
"""

from __future__ import annotations

import json
import secrets
from datetime import datetime, timezone


def generate_secret(nbytes: int = 32) -> str:
    """Generate a cryptographically random hex secret with >= 256-bit entropy."""
    return secrets.token_hex(nbytes)


def generate_deployment_secrets() -> dict[str, str]:
    """Generate all secrets needed for a fresh Hub deployment."""
    return {
        "jwt_secret": generate_secret(),
        "session_secret": generate_secret(),
        "oidc_hmac_secret": generate_secret(),
        "oidc_client_secret": generate_secret(),
        "redis_password": generate_secret(),
        "db_password": generate_secret(),
        "mqtt_admin_password": generate_secret(),
    }


def log_security_event(
    event_type: str,
    source_ip: str,
    user: str | None = None,
    resource: str | None = None,
    details: str | None = None,
) -> str:
    """Return a structured JSON log line for a security event."""
    entry = {
        "event_type": event_type,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "source_ip": source_ip,
        "user": user,
        "resource": resource,
        "details": details,
    }
    return json.dumps(entry)
