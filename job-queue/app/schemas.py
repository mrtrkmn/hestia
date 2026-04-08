"""Request/response schemas for the Job Queue REST API."""

from pydantic import BaseModel

from shared.models.jobs import Job, JobStatus


class JobListResponse(BaseModel):
    """Paginated list of jobs."""

    jobs: list[Job]
    total: int
    limit: int
    offset: int


class JobResponse(BaseModel):
    """Single job detail response."""

    job: Job


class CancelResponse(BaseModel):
    """Response after cancelling a job."""

    job: Job
    message: str


class ErrorResponse(BaseModel):
    """Standard error body."""

    error: str
    message: str
    details: dict | None = None
