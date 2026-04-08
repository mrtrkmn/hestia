"""Job Queue REST API — internal endpoints consumed by the API Gateway.

Exposes:
  GET    /jobs          — list jobs (optional ?status, ?limit, ?offset)
  GET    /jobs/{job_id} — get job by ID
  DELETE /jobs/{job_id} — cancel a pending job
"""

from __future__ import annotations

from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends, FastAPI, HTTPException, Query

from app.config import get_settings
from app.queue import JobQueue
from app.schemas import (
    CancelResponse,
    ErrorResponse,
    JobListResponse,
    JobResponse,
)
from shared.models.jobs import JobStatus

app = FastAPI(title="Job Queue Service", version="0.1.0")

# ---------------------------------------------------------------------------
# Dependency injection
# ---------------------------------------------------------------------------

_redis_client: aioredis.Redis | None = None


async def _get_redis() -> aioredis.Redis:
    global _redis_client
    if _redis_client is None:
        settings = get_settings()
        _redis_client = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis_client


async def _get_queue(
    redis_client: Annotated[aioredis.Redis, Depends(_get_redis)],
) -> JobQueue:
    return JobQueue(redis_client)


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------


@app.get("/jobs", response_model=JobListResponse)
async def list_jobs(
    queue: Annotated[JobQueue, Depends(_get_queue)],
    status: str | None = Query(default=None, description="Filter by job status"),
    limit: int = Query(default=50, ge=1, le=200, description="Max results"),
    offset: int = Query(default=0, ge=0, description="Pagination offset"),
) -> JobListResponse:
    """List jobs with optional status filter and pagination."""
    status_filter: JobStatus | None = None
    if status is not None:
        try:
            status_filter = JobStatus(status)
        except ValueError:
            valid = [s.value for s in JobStatus]
            raise HTTPException(
                status_code=400,
                detail=f"Invalid status '{status}'. Must be one of {valid}",
            )

    jobs = await queue.list_jobs(status_filter=status_filter, limit=limit, offset=offset)
    return JobListResponse(jobs=jobs, total=len(jobs), limit=limit, offset=offset)


@app.get(
    "/jobs/{job_id}",
    response_model=JobResponse,
    responses={404: {"model": ErrorResponse}},
)
async def get_job(
    job_id: str,
    queue: Annotated[JobQueue, Depends(_get_queue)],
) -> JobResponse:
    """Get a single job by ID."""
    job = await queue.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")
    return JobResponse(job=job)


@app.delete(
    "/jobs/{job_id}",
    response_model=CancelResponse,
    responses={
        404: {"model": ErrorResponse},
        409: {"model": ErrorResponse},
    },
)
async def cancel_job(
    job_id: str,
    queue: Annotated[JobQueue, Depends(_get_queue)],
) -> CancelResponse:
    """Cancel a pending job. Returns 409 if the job is not in a cancellable state."""
    job = await queue.get_job(job_id)
    if job is None:
        raise HTTPException(status_code=404, detail=f"Job '{job_id}' not found")

    if job.status != JobStatus.PENDING:
        raise HTTPException(
            status_code=409,
            detail=f"Job '{job_id}' is '{job.status.value}' and cannot be cancelled. Only pending jobs can be cancelled.",
        )

    cancelled = await queue.cancel(job_id)
    if cancelled is None:  # pragma: no cover
        raise HTTPException(status_code=409, detail="Job could not be cancelled")

    return CancelResponse(job=cancelled, message="Job cancelled successfully")
