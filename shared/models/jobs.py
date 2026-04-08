"""Job queue data models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class JobStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobPriority(str, Enum):
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"


class Job(BaseModel):
    id: str
    type: str
    status: JobStatus
    priority: JobPriority
    input_files: list[str]
    output_file: str | None
    parameters: dict
    progress: int
    error: str | None
    retries: int
    created_at: datetime
    updated_at: datetime
    completed_at: datetime | None
    user_id: str
