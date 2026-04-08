"""MQTT credential management for Hestia.

Manages username/password credentials for MQTT clients, backed by
the Hub's user directory.

Requirement 10.6
"""

from __future__ import annotations

import hashlib
import hmac
import os


class MQTTCredentialStore:
    """In-memory MQTT credential store backed by the Hub user directory."""

    def __init__(self) -> None:
        self._credentials: dict[str, bytes] = {}  # username -> hashed password

    @staticmethod
    def _hash(password: str, salt: bytes) -> bytes:
        return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 100_000)

    def add_user(self, username: str, password: str) -> None:
        salt = os.urandom(16)
        hashed = self._hash(password, salt)
        self._credentials[username] = salt + hashed

    def remove_user(self, username: str) -> bool:
        return self._credentials.pop(username, None) is not None

    def authenticate(self, username: str, password: str) -> bool:
        stored = self._credentials.get(username)
        if stored is None:
            return False
        salt, expected = stored[:16], stored[16:]
        return hmac.compare_digest(self._hash(password, salt), expected)

    def has_user(self, username: str) -> bool:
        return username in self._credentials
