"""User and authentication data models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class UserRole(str, Enum):
    ADMIN = "admin"
    USER = "user"


class User(BaseModel):
    id: str
    username: str
    email: str
    role: UserRole
    totp_enabled: bool
    locked_until: datetime | None
    failed_attempts: int
    created_at: datetime


class AuthToken(BaseModel):
    access_token: str
    token_type: str
    expires_in: int
