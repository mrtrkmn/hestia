"""Unit tests for the Worker process."""

import asyncio
import sys
import os
import time

import fakeredis.aioredis
import pytest
import pytest_asyncio

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.models.jobs import Job, JobPriority, JobStatus
from app.queue import JobQueue, _QUEUE_KEY, _job_key, _compute_score, _JOB_TTL_SECONDS
from app.worker import (
    Worker,
    ProcessorRegistry,
    ProgressCallback,
    _heartbeat_key,
    _HEARTBEAT_TIMEOUT,
    _MAX_RETRIES,
)


@pytest_asyncio.fixture
async def redis_client():
    client = fakeredis.aioredis.FakeRedis(decode_responses=False)
    yield client
    await client.flushall()
    await client.aclose()


@pytest_asyncio.fixture
async def queue(redis_client):
    return JobQueue(redis_client)


# ------------------------------------------------------------------
# ProcessorRegistry tests
# ------------------------------------------------------------------


class TestProcessorRegistry:
    def test_register_and_get(self):
        registry = ProcessorRegistry()

        async def handler(job: Job, cb: ProgressCallback) -> str:
            return "/out.pdf"

        registry.register("pdf_merge", handler)
        assert registry.get("pdf_merge") is handler
        assert "pdf_merge" in registry

    def test_get_missing(self):
        registry = ProcessorRegistry()
        assert registry.get("nonexistent") is None
        assert "nonexistent" not in registry


# ------------------------------------------------------------------
# Worker execution tests
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_worker_processes_job_to_completion(redis_client, queue: JobQueue):
    """Worker should execute a job, report progress, and mark completed."""
    registry = ProcessorRegistry()
    progress_values: list[int] = []

    async def fake_handler(job: Job, progress_cb: ProgressCallback) -> str:
        await progress_cb(25)
        progress_values.append(25)
        await progress_cb(75)
        progress_values.append(75)
        return "/output/result.pdf"

    registry.register("pdf_merge", fake_handler)

    job_id = await queue.enqueue("pdf_merge", ["/a.pdf"], {}, "user1")

    worker = Worker(queue, redis_client, registry, poll_interval=0.05)

    async def stop_after_processing():
        # Wait until the job is completed
        for _ in range(100):
            job = await queue.get_job(job_id)
            if job and job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
                await worker.stop()
                return
            await asyncio.sleep(0.05)
        await worker.stop()

    stop_task = asyncio.create_task(stop_after_processing())
    await asyncio.wait_for(worker.start(), timeout=5.0)
    await stop_task

    job = await queue.get_job(job_id)
    assert job is not None
    assert job.status == JobStatus.COMPLETED
    assert job.output_file == "/output/result.pdf"
    assert job.progress == 100
    assert job.completed_at is not None
    assert 25 in progress_values
    assert 75 in progress_values


@pytest.mark.asyncio
async def test_worker_marks_failed_on_exception(redis_client, queue: JobQueue):
    """Worker should mark job as failed when handler raises."""
    registry = ProcessorRegistry()

    async def failing_handler(job: Job, progress_cb: ProgressCallback) -> str:
        raise RuntimeError("Something went wrong")

    registry.register("bad_op", failing_handler)

    job_id = await queue.enqueue("bad_op", ["/a.pdf"], {}, "user1")

    worker = Worker(queue, redis_client, registry, poll_interval=0.05)

    async def stop_after_processing():
        for _ in range(100):
            job = await queue.get_job(job_id)
            if job and job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
                await worker.stop()
                return
            await asyncio.sleep(0.05)
        await worker.stop()

    stop_task = asyncio.create_task(stop_after_processing())
    await asyncio.wait_for(worker.start(), timeout=5.0)
    await stop_task

    job = await queue.get_job(job_id)
    assert job is not None
    assert job.status == JobStatus.FAILED
    assert job.error == "Something went wrong"


@pytest.mark.asyncio
async def test_worker_unknown_job_type(redis_client, queue: JobQueue):
    """Worker should fail jobs with unregistered types."""
    registry = ProcessorRegistry()

    job_id = await queue.enqueue("unknown_type", ["/a.pdf"], {}, "user1")

    worker = Worker(queue, redis_client, registry, poll_interval=0.05)

    async def stop_after_processing():
        for _ in range(100):
            job = await queue.get_job(job_id)
            if job and job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
                await worker.stop()
                return
            await asyncio.sleep(0.05)
        await worker.stop()

    stop_task = asyncio.create_task(stop_after_processing())
    await asyncio.wait_for(worker.start(), timeout=5.0)
    await stop_task

    job = await queue.get_job(job_id)
    assert job is not None
    assert job.status == JobStatus.FAILED
    assert "Unknown job type" in (job.error or "")


@pytest.mark.asyncio
async def test_worker_heartbeat_set_during_processing(redis_client, queue: JobQueue):
    """Worker should set a heartbeat key in Redis while processing."""
    registry = ProcessorRegistry()
    heartbeat_seen = False

    async def slow_handler(job: Job, progress_cb: ProgressCallback) -> str:
        nonlocal heartbeat_seen
        # Give heartbeat loop time to fire
        await asyncio.sleep(0.3)
        val = await redis_client.get(_heartbeat_key(job.id))
        heartbeat_seen = val is not None
        return "/out.pdf"

    registry.register("slow_op", slow_handler)

    job_id = await queue.enqueue("slow_op", [], {}, "user1")

    worker = Worker(queue, redis_client, registry, poll_interval=0.05)

    async def stop_after_processing():
        for _ in range(200):
            job = await queue.get_job(job_id)
            if job and job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
                await worker.stop()
                return
            await asyncio.sleep(0.05)
        await worker.stop()

    stop_task = asyncio.create_task(stop_after_processing())
    await asyncio.wait_for(worker.start(), timeout=10.0)
    await stop_task

    assert heartbeat_seen, "Heartbeat should have been set in Redis during processing"


@pytest.mark.asyncio
async def test_worker_cleans_heartbeat_after_completion(redis_client, queue: JobQueue):
    """Heartbeat key should be removed after job finishes."""
    registry = ProcessorRegistry()

    async def quick_handler(job: Job, progress_cb: ProgressCallback) -> str:
        return "/out.pdf"

    registry.register("quick_op", quick_handler)

    job_id = await queue.enqueue("quick_op", [], {}, "user1")

    worker = Worker(queue, redis_client, registry, poll_interval=0.05)

    async def stop_after_processing():
        for _ in range(100):
            job = await queue.get_job(job_id)
            if job and job.status in (JobStatus.COMPLETED, JobStatus.FAILED):
                await worker.stop()
                return
            await asyncio.sleep(0.05)
        await worker.stop()

    stop_task = asyncio.create_task(stop_after_processing())
    await asyncio.wait_for(worker.start(), timeout=5.0)
    await stop_task

    val = await redis_client.get(_heartbeat_key(job_id))
    assert val is None, "Heartbeat key should be cleaned up after job completion"


# ------------------------------------------------------------------
# Stale heartbeat / re-enqueue tests
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_handle_stale_job_requeues(redis_client, queue: JobQueue):
    """A stale RUNNING job should be re-enqueued with incremented retries."""
    job_id = await queue.enqueue("op", [], {}, "user1")
    # Manually set to RUNNING (simulating a worker that crashed)
    await queue.update_status(job_id, JobStatus.RUNNING)

    registry = ProcessorRegistry()
    worker = Worker(queue, redis_client, registry)

    # Simulate stale heartbeat
    await redis_client.set(
        _heartbeat_key(job_id),
        str(time.time() - _HEARTBEAT_TIMEOUT - 10),
    )

    await worker._handle_stale_job(job_id)

    job = await queue.get_job(job_id)
    assert job is not None
    assert job.status == JobStatus.PENDING
    assert job.retries == 1


@pytest.mark.asyncio
async def test_handle_stale_job_fails_after_max_retries(redis_client, queue: JobQueue):
    """A stale job that has exhausted retries should be marked failed."""
    job_id = await queue.enqueue("op", [], {}, "user1")
    await queue.update_status(job_id, JobStatus.RUNNING)

    # Set retries to max
    job = await queue.get_job(job_id)
    assert job is not None
    job.retries = _MAX_RETRIES
    await redis_client.set(_job_key(job_id), job.model_dump_json())

    registry = ProcessorRegistry()
    worker = Worker(queue, redis_client, registry)

    await worker._handle_stale_job(job_id)

    job = await queue.get_job(job_id)
    assert job is not None
    assert job.status == JobStatus.FAILED
    assert "maximum retries" in (job.error or "").lower()


@pytest.mark.asyncio
async def test_handle_stale_job_ignores_non_running(redis_client, queue: JobQueue):
    """Stale heartbeat check should ignore jobs not in RUNNING state."""
    job_id = await queue.enqueue("op", [], {}, "user1")
    # Job is PENDING, not RUNNING

    registry = ProcessorRegistry()
    worker = Worker(queue, redis_client, registry)

    await worker._handle_stale_job(job_id)

    job = await queue.get_job(job_id)
    assert job is not None
    assert job.status == JobStatus.PENDING  # unchanged


@pytest.mark.asyncio
async def test_requeue_job_adds_back_to_queue(redis_client, queue: JobQueue):
    """_requeue_job should put the job back in the sorted set."""
    job_id = await queue.enqueue("op", [], {}, "user1")
    job = await queue.dequeue()  # pops from queue, marks RUNNING
    assert job is not None

    registry = ProcessorRegistry()
    worker = Worker(queue, redis_client, registry)

    await worker._requeue_job(job)

    # Should be dequeueable again
    requeued = await queue.dequeue()
    assert requeued is not None
    assert requeued.id == job_id
    assert requeued.retries == 1


@pytest.mark.asyncio
async def test_worker_processes_multiple_jobs_sequentially(redis_client, queue: JobQueue):
    """Worker should process multiple queued jobs one after another."""
    registry = ProcessorRegistry()
    processed_ids: list[str] = []

    async def tracking_handler(job: Job, progress_cb: ProgressCallback) -> str:
        processed_ids.append(job.id)
        return f"/out/{job.id}.pdf"

    registry.register("track_op", tracking_handler)

    id1 = await queue.enqueue("track_op", [], {}, "user1")
    id2 = await queue.enqueue("track_op", [], {}, "user1")

    worker = Worker(queue, redis_client, registry, poll_interval=0.05)

    async def stop_after_both():
        for _ in range(200):
            j1 = await queue.get_job(id1)
            j2 = await queue.get_job(id2)
            if (j1 and j1.status == JobStatus.COMPLETED and
                    j2 and j2.status == JobStatus.COMPLETED):
                await worker.stop()
                return
            await asyncio.sleep(0.05)
        await worker.stop()

    stop_task = asyncio.create_task(stop_after_both())
    await asyncio.wait_for(worker.start(), timeout=5.0)
    await stop_task

    assert id1 in processed_ids
    assert id2 in processed_ids
