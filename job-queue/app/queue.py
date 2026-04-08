"""Redis-backed job queue with priority-based FIFO dispatch.

Uses Redis sorted sets for ordering (score = priority_weight * 1e12 + timestamp)
and Redis hashes for job data storage. Jobs have a 7-day TTL for automatic cleanup.
"""

import time
import uuid
from datetime import datetime, timezone

import redis.asyncio as redis

from shared.models.jobs import Job, JobPriority, JobStatus

# Priority weights: lower score = dispatched first
_PRIORITY_WEIGHTS: dict[JobPriority, int] = {
    JobPriority.HIGH: 0,
    JobPriority.NORMAL: 1,
    JobPriority.LOW: 2,
}

_QUEUE_KEY = "hub:job_queue"
_JOB_PREFIX = "hub:job:"
_SEQUENCE_KEY = "hub:job_queue:seq"
_JOB_TTL_SECONDS = 7 * 24 * 60 * 60  # 7 days


def _job_key(job_id: str) -> str:
    return f"{_JOB_PREFIX}{job_id}"


def _compute_score(priority: JobPriority, sequence: int) -> float:
    """Compute sorted-set score: lower = dispatched sooner.

    priority_weight * 1e12 groups by priority, then a monotonic sequence
    number guarantees strict FIFO within the same priority band.
    """
    return _PRIORITY_WEIGHTS[priority] * 1e12 + sequence


class JobQueue:
    """Async Redis-backed job queue."""

    def __init__(self, redis_client: redis.Redis) -> None:
        self._redis = redis_client

    # ------------------------------------------------------------------
    # Enqueue
    # ------------------------------------------------------------------

    async def enqueue(
        self,
        type: str,
        input_files: list[str],
        parameters: dict,
        user_id: str,
        priority: JobPriority = JobPriority.NORMAL,
    ) -> str:
        """Create a new job and add it to the queue.

        Returns the unique job ID (UUID).
        """
        job_id = str(uuid.uuid4())
        now = datetime.now(timezone.utc)

        job = Job(
            id=job_id,
            type=type,
            status=JobStatus.PENDING,
            priority=priority,
            input_files=input_files,
            output_file=None,
            parameters=parameters,
            progress=0,
            error=None,
            retries=0,
            created_at=now,
            updated_at=now,
            completed_at=None,
            user_id=user_id,
        )

        pipe = self._redis.pipeline()
        # Store job data as JSON in a hash field
        pipe.set(_job_key(job_id), job.model_dump_json())
        pipe.expire(_job_key(job_id), _JOB_TTL_SECONDS)
        await pipe.execute()

        # Use atomic Redis counter for strict FIFO ordering within priority
        seq = await self._redis.incr(_SEQUENCE_KEY)
        score = _compute_score(priority, seq)
        await self._redis.zadd(_QUEUE_KEY, {job_id: score})
        await pipe.execute()

        return job_id

    # ------------------------------------------------------------------
    # Dequeue
    # ------------------------------------------------------------------

    async def dequeue(self) -> Job | None:
        """Remove and return the next job by priority (HIGH > NORMAL > LOW).

        Within the same priority level, jobs are returned in FIFO order.
        Returns None if the queue is empty.
        """
        # Pop the member with the lowest score (highest priority, earliest time)
        results = await self._redis.zpopmin(_QUEUE_KEY, count=1)
        if not results:
            return None

        job_id_bytes, _score = results[0]
        job_id = job_id_bytes if isinstance(job_id_bytes, str) else job_id_bytes.decode()

        job = await self.get_job(job_id)
        if job is None:
            return None

        # Mark as running
        await self.update_status(job_id, JobStatus.RUNNING)
        return await self.get_job(job_id)

    # ------------------------------------------------------------------
    # Get / Query
    # ------------------------------------------------------------------

    async def get_job(self, job_id: str) -> Job | None:
        """Retrieve a job by ID, or None if not found."""
        data = await self._redis.get(_job_key(job_id))
        if data is None:
            return None
        raw = data if isinstance(data, str) else data.decode()
        return Job.model_validate_json(raw)

    # ------------------------------------------------------------------
    # Update
    # ------------------------------------------------------------------

    async def update_status(
        self,
        job_id: str,
        status: JobStatus,
        progress: int | None = None,
        output_file: str | None = None,
        error: str | None = None,
    ) -> Job | None:
        """Update a job's status and optional fields. Returns updated Job or None."""
        job = await self.get_job(job_id)
        if job is None:
            return None

        now = datetime.now(timezone.utc)
        job.status = status
        job.updated_at = now

        if progress is not None:
            job.progress = progress
        if output_file is not None:
            job.output_file = output_file
        if error is not None:
            job.error = error
        if status == JobStatus.COMPLETED:
            job.completed_at = now
            job.progress = 100

        pipe = self._redis.pipeline()
        pipe.set(_job_key(job_id), job.model_dump_json())
        pipe.expire(_job_key(job_id), _JOB_TTL_SECONDS)
        await pipe.execute()

        return job

    # ------------------------------------------------------------------
    # Cancel
    # ------------------------------------------------------------------

    async def cancel(self, job_id: str) -> Job | None:
        """Cancel a pending job. Only PENDING jobs can be cancelled.

        Returns the updated Job, or None if not found or not cancellable.
        """
        job = await self.get_job(job_id)
        if job is None:
            return None
        if job.status != JobStatus.PENDING:
            return None

        # Remove from the dispatch queue
        await self._redis.zrem(_QUEUE_KEY, job_id)
        return await self.update_status(job_id, JobStatus.CANCELLED)

    # ------------------------------------------------------------------
    # List
    # ------------------------------------------------------------------

    async def list_jobs(
        self,
        status_filter: JobStatus | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> list[Job]:
        """List jobs, optionally filtered by status.

        Scans all job keys. For production scale a secondary index would be
        preferable, but for a single-machine home hub this is fine.
        """
        cursor: int | bytes = 0
        jobs: list[Job] = []

        while True:
            cursor, keys = await self._redis.scan(
                cursor=int(cursor) if isinstance(cursor, (int, bytes)) else 0,
                match=f"{_JOB_PREFIX}*",
                count=200,
            )
            for key in keys:
                data = await self._redis.get(key)
                if data is None:
                    continue
                raw = data if isinstance(data, str) else data.decode()
                job = Job.model_validate_json(raw)
                if status_filter is None or job.status == status_filter:
                    jobs.append(job)
            if cursor == 0 or cursor == b"0":
                break

        # Sort by created_at descending (newest first)
        jobs.sort(key=lambda j: j.created_at, reverse=True)
        return jobs[offset : offset + limit]

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    async def cleanup_expired(self) -> int:
        """Remove jobs older than 7 days. Returns count of removed jobs."""
        cutoff = time.time() - _JOB_TTL_SECONDS
        removed = 0
        cursor: int | bytes = 0

        while True:
            cursor, keys = await self._redis.scan(
                cursor=int(cursor) if isinstance(cursor, (int, bytes)) else 0,
                match=f"{_JOB_PREFIX}*",
                count=200,
            )
            for key in keys:
                data = await self._redis.get(key)
                if data is None:
                    continue
                raw = data if isinstance(data, str) else data.decode()
                job = Job.model_validate_json(raw)
                if job.created_at.timestamp() < cutoff:
                    job_id = job.id
                    pipe = self._redis.pipeline()
                    pipe.delete(_job_key(job_id))
                    pipe.zrem(_QUEUE_KEY, job_id)
                    await pipe.execute()
                    removed += 1
            if cursor == 0 or cursor == b"0":
                break

        return removed
