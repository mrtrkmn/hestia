"""Job management routes.

Requirements: 13.8
"""

from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/jobs", tags=["jobs"])


@router.get("")
async def list_jobs(status: str | None = None):
    return {"jobs": []}


@router.get("/{job_id}")
async def get_job(job_id: str):
    return {"job_id": job_id}


@router.delete("/{job_id}")
async def cancel_job(job_id: str):
    return {"job_id": job_id, "status": "cancelled"}
