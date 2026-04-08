"""Worker process that consumes jobs from the Redis-backed queue.

Responsibilities:
- Poll the JobQueue for available jobs
- Dispatch jobs to registered processor functions
- Report progress every ≤5 seconds
- Store output file reference on completion, mark status "completed"
- Heartbeat-based crash detection (30s timeout) with re-enqueue (up to 3 retries)
"""

import asyncio
import logging
import time
from typing import Callable, Awaitable

import redis.asyncio as redis

from shared.models.jobs import Job, JobStatus
from app.queue import JobQueue

logger = logging.getLogger(__name__)

# Type alias for processor handler functions
ProgressCallback = Callable[[int], Awaitable[None]]
ProcessorHandler = Callable[[Job, ProgressCallback], Awaitable[str]]

_HEARTBEAT_PREFIX = "hub:worker:heartbeat:"
_HEARTBEAT_INTERVAL = 10  # seconds
_HEARTBEAT_TIMEOUT = 30  # seconds
_MAX_RETRIES = 3


def _heartbeat_key(job_id: str) -> str:
    return f"{_HEARTBEAT_PREFIX}{job_id}"


class ProcessorRegistry:
    """Maps job types to async handler functions."""

    def __init__(self) -> None:
        self._handlers: dict[str, ProcessorHandler] = {}

    def register(self, job_type: str, handler: ProcessorHandler) -> None:
        self._handlers[job_type] = handler

    def get(self, job_type: str) -> ProcessorHandler | None:
        return self._handlers.get(job_type)

    def __contains__(self, job_type: str) -> bool:
        return job_type in self._handlers


class Worker:
    """Consumes jobs from the queue, executes them, and manages heartbeats."""

    def __init__(
        self,
        queue: JobQueue,
        redis_client: redis.Redis,
        registry: ProcessorRegistry,
        poll_interval: float = 1.0,
    ) -> None:
        self._queue = queue
        self._redis = redis_client
        self._registry = registry
        self._poll_interval = poll_interval
        self._running = False

    async def start(self) -> None:
        """Start the worker loop and stale-heartbeat monitor."""
        self._running = True
        logger.info("Worker started")
        monitor_task = asyncio.create_task(self._monitor_stale_heartbeats())
        try:
            await self._poll_loop()
        finally:
            self._running = False
            monitor_task.cancel()
            try:
                await monitor_task
            except asyncio.CancelledError:
                pass
            logger.info("Worker stopped")

    async def stop(self) -> None:
        self._running = False

    # ------------------------------------------------------------------
    # Main poll loop
    # ------------------------------------------------------------------

    async def _poll_loop(self) -> None:
        while self._running:
            job = await self._queue.dequeue()
            if job is None:
                await asyncio.sleep(self._poll_interval)
                continue
            await self._execute_job(job)

    # ------------------------------------------------------------------
    # Job execution
    # ------------------------------------------------------------------

    async def _execute_job(self, job: Job) -> None:
        handler = self._registry.get(job.type)
        if handler is None:
            logger.error("No handler registered for job type %s", job.type)
            await self._queue.update_status(
                job.id, JobStatus.FAILED, error=f"Unknown job type: {job.type}"
            )
            return

        # Start heartbeat
        heartbeat_task = asyncio.create_task(self._heartbeat_loop(job.id))

        last_progress_time = time.monotonic()
        last_progress_value = 0

        async def progress_callback(progress: int) -> None:
            nonlocal last_progress_time, last_progress_value
            now = time.monotonic()
            last_progress_value = progress
            # Always report — the caller is responsible for calling at ≤5s intervals
            last_progress_time = now
            await self._queue.update_status(job.id, JobStatus.RUNNING, progress=progress)

        try:
            output_file = await handler(job, progress_callback)
            await self._queue.update_status(
                job.id, JobStatus.COMPLETED, output_file=output_file
            )
            logger.info("Job %s completed, output: %s", job.id, output_file)
        except Exception as exc:
            logger.exception("Job %s failed: %s", job.id, exc)
            await self._queue.update_status(
                job.id, JobStatus.FAILED, error=str(exc)
            )
        finally:
            heartbeat_task.cancel()
            try:
                await heartbeat_task
            except asyncio.CancelledError:
                pass
            # Clean up heartbeat key
            await self._redis.delete(_heartbeat_key(job.id))

    # ------------------------------------------------------------------
    # Heartbeat
    # ------------------------------------------------------------------

    async def _heartbeat_loop(self, job_id: str) -> None:
        """Send heartbeat to Redis every HEARTBEAT_INTERVAL seconds."""
        key = _heartbeat_key(job_id)
        try:
            while True:
                await self._redis.set(key, str(time.time()), ex=_HEARTBEAT_TIMEOUT)
                await asyncio.sleep(_HEARTBEAT_INTERVAL)
        except asyncio.CancelledError:
            return

    async def _monitor_stale_heartbeats(self) -> None:
        """Periodically scan for stale heartbeats and re-enqueue those jobs."""
        try:
            while self._running:
                await asyncio.sleep(_HEARTBEAT_INTERVAL)
                await self._check_stale_heartbeats()
        except asyncio.CancelledError:
            return

    async def _check_stale_heartbeats(self) -> None:
        """Find RUNNING jobs whose heartbeat has expired and re-enqueue them."""
        cursor: int | bytes = 0
        while True:
            cursor, keys = await self._redis.scan(
                cursor=int(cursor) if isinstance(cursor, (int, bytes)) else 0,
                match=f"{_HEARTBEAT_PREFIX}*",
                count=100,
            )
            for key in keys:
                key_str = key if isinstance(key, str) else key.decode()
                job_id = key_str.removeprefix(_HEARTBEAT_PREFIX)
                val = await self._redis.get(key)
                if val is None:
                    # Heartbeat expired (TTL elapsed) — check if job is still RUNNING
                    await self._handle_stale_job(job_id)
                else:
                    ts = float(val if isinstance(val, str) else val.decode())
                    if time.time() - ts > _HEARTBEAT_TIMEOUT:
                        await self._handle_stale_job(job_id)
            if cursor == 0 or cursor == b"0":
                break

    async def _handle_stale_job(self, job_id: str) -> None:
        """Re-enqueue a stale job or mark it failed after max retries."""
        job = await self._queue.get_job(job_id)
        if job is None or job.status != JobStatus.RUNNING:
            # Clean up orphan heartbeat
            await self._redis.delete(_heartbeat_key(job_id))
            return

        if job.retries >= _MAX_RETRIES:
            logger.warning("Job %s exceeded max retries (%d), marking failed", job_id, _MAX_RETRIES)
            await self._queue.update_status(
                job_id, JobStatus.FAILED, error="Exceeded maximum retries after worker crash"
            )
            await self._redis.delete(_heartbeat_key(job_id))
            return

        logger.info("Re-enqueueing stale job %s (retry %d)", job_id, job.retries + 1)
        await self._requeue_job(job)

    async def _requeue_job(self, job: Job) -> None:
        """Put a job back in the queue with incremented retry count."""
        # Increment retries on the job record
        job.retries += 1
        job.status = JobStatus.PENDING
        # Persist updated job
        from app.queue import _job_key, _compute_score, _QUEUE_KEY, _JOB_TTL_SECONDS
        pipe = self._redis.pipeline()
        pipe.set(_job_key(job.id), job.model_dump_json())
        pipe.expire(_job_key(job.id), _JOB_TTL_SECONDS)
        await pipe.execute()
        # Re-add to sorted set
        seq = await self._redis.incr("hub:job_queue:seq")
        score = _compute_score(job.priority, seq)
        await self._redis.zadd(_QUEUE_KEY, {job.id: score})
        # Remove heartbeat
        await self._redis.delete(_heartbeat_key(job.id))


async def run_worker(
    redis_url: str = "redis://localhost:6379/0",
    registry: ProcessorRegistry | None = None,
    poll_interval: float = 1.0,
) -> None:
    """Entry point for running a worker process."""
    client = redis.from_url(redis_url)
    queue = JobQueue(client)
    if registry is None:
        registry = ProcessorRegistry()
    worker = Worker(queue, client, registry, poll_interval=poll_interval)
    try:
        await worker.start()
    finally:
        await client.aclose()
