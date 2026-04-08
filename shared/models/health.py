"""Service health data models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class ServiceStatus(str, Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    OFFLINE = "offline"


class ServiceHealth(BaseModel):
    name: str
    status: ServiceStatus
    uptime_seconds: int
    last_check: datetime
    details: dict | None
