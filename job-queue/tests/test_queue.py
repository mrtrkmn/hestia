"""Unit tests for the Redis-backed JobQueue."""

import asyncio
import time

import fakeredis.aioredis
import pytest
import pytest_asyncio

import sys
import os

# Add job-queue directory to path so we can import app.queue
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from shared.models.jobs import JobPriority, JobStatus
from app.queue import JobQueue


@pytest_asyncio.fixture
async def redis_client():
    client = fakeredis.aioredis.FakeRedis(decode_responses=False)
    yield client
    await client.flushall()
    await client.aclose()


@pytest_asyncio.fixture
async def queue(redis_client):
    return JobQueue(redis_client)


@pytest.mark.asyncio
async def test_enqueue_returns_unique_id(queue: JobQueue):
    """Enqueue should return a unique UUID string."""
    id1 = await queue.enqueue("pdf_merge", ["/a.pdf"], {}, "user1")
    id2 = await queue.enqueue("pdf_merge", ["/b.pdf"], {}, "user1")
    assert isinstance(id1, str)
    assert len(id1) == 36  # UUID format
    assert id1 != id2


@pytest.mark.asyncio
async def test_enqueue_creates_pending_job(queue: JobQueue):
    """Enqueued job should be retrievable with PENDING status."""
    job_id = await queue.enqueue("image_convert", ["/img.png"], {"format": "jpeg"}, "user1")
    job = await queue.get_job(job_id)
    assert job is not None
    assert job.id == job_id
    assert job.status == JobStatus.PENDING
    assert job.type == "image_convert"
    assert job.input_files == ["/img.png"]
    assert job.parameters == {"format": "jpeg"}
    assert job.user_id == "user1"
    assert job.progress == 0
    assert job.output_file is None
    assert job.error is None


@pytest.mark.asyncio
async def test_dequeue_returns_none_on_empty(queue: JobQueue):
    """Dequeue on empty queue should return None."""
    result = await queue.dequeue()
    assert result is None


@pytest.mark.asyncio
async def test_dequeue_fifo_same_priority(queue: JobQueue):
    """Jobs with the same priority should be dequeued in FIFO order."""
    id1 = await queue.enqueue("op", [], {}, "u", JobPriority.NORMAL)
    id2 = await queue.enqueue("op", [], {}, "u", JobPriority.NORMAL)
    id3 = await queue.enqueue("op", [], {}, "u", JobPriority.NORMAL)

    j1 = await queue.dequeue()
    j2 = await queue.dequeue()
    j3 = await queue.dequeue()

    assert j1 is not None and j1.id == id1
    assert j2 is not None and j2.id == id2
    assert j3 is not None and j3.id == id3


@pytest.mark.asyncio
async def test_dequeue_priority_ordering(queue: JobQueue):
    """HIGH priority jobs should be dequeued before NORMAL, NORMAL before LOW."""
    id_low = await queue.enqueue("op", [], {}, "u", JobPriority.LOW)
    id_normal = await queue.enqueue("op", [], {}, "u", JobPriority.NORMAL)
    id_high = await queue.enqueue("op", [], {}, "u", JobPriority.HIGH)

    j1 = await queue.dequeue()
    j2 = await queue.dequeue()
    j3 = await queue.dequeue()

    assert j1 is not None and j1.id == id_high
    assert j2 is not None and j2.id == id_normal
    assert j3 is not None and j3.id == id_low


@pytest.mark.asyncio
async def test_dequeue_marks_running(queue: JobQueue):
    """Dequeued job should have RUNNING status."""
    await queue.enqueue("op", [], {}, "u")
    job = await queue.dequeue()
    assert job is not None
    assert job.status == JobStatus.RUNNING


@pytest.mark.asyncio
async def test_get_job_not_found(queue: JobQueue):
    """get_job should return None for non-existent ID."""
    assert await queue.get_job("nonexistent-id") is None


@pytest.mark.asyncio
async def test_update_status(queue: JobQueue):
    """update_status should modify job fields correctly."""
    job_id = await queue.enqueue("op", [], {}, "u")
    updated = await queue.update_status(
        job_id, JobStatus.RUNNING, progress=50
    )
    assert updated is not None
    assert updated.status == JobStatus.RUNNING
    assert updated.progress == 50


@pytest.mark.asyncio
async def test_update_status_completed(queue: JobQueue):
    """Completing a job should set progress=100 and completed_at."""
    job_id = await queue.enqueue("op", [], {}, "u")
    updated = await queue.update_status(
        job_id, JobStatus.COMPLETED, output_file="/out.pdf"
    )
    assert updated is not None
    assert updated.status == JobStatus.COMPLETED
    assert updated.progress == 100
    assert updated.output_file == "/out.pdf"
    assert updated.completed_at is not None


@pytest.mark.asyncio
async def test_update_status_nonexistent(queue: JobQueue):
    """update_status on missing job should return None."""
    assert await queue.update_status("missing", JobStatus.RUNNING) is None


@pytest.mark.asyncio
async def test_cancel_pending_job(queue: JobQueue):
    """Cancelling a PENDING job should set status to CANCELLED."""
    job_id = await queue.enqueue("op", [], {}, "u")
    cancelled = await queue.cancel(job_id)
    assert cancelled is not None
    assert cancelled.status == JobStatus.CANCELLED

    # Should not be dequeued anymore
    assert await queue.dequeue() is None


@pytest.mark.asyncio
async def test_cancel_running_job_fails(queue: JobQueue):
    """Only PENDING jobs can be cancelled."""
    job_id = await queue.enqueue("op", [], {}, "u")
    await queue.update_status(job_id, JobStatus.RUNNING)
    result = await queue.cancel(job_id)
    assert result is None


@pytest.mark.asyncio
async def test_cancel_nonexistent_job(queue: JobQueue):
    """Cancelling a non-existent job should return None."""
    assert await queue.cancel("nonexistent") is None


@pytest.mark.asyncio
async def test_list_jobs_all(queue: JobQueue):
    """list_jobs without filter should return all jobs."""
    await queue.enqueue("a", [], {}, "u")
    await queue.enqueue("b", [], {}, "u")
    await queue.enqueue("c", [], {}, "u")

    jobs = await queue.list_jobs()
    assert len(jobs) == 3


@pytest.mark.asyncio
async def test_list_jobs_with_status_filter(queue: JobQueue):
    """list_jobs with status filter should only return matching jobs."""
    id1 = await queue.enqueue("a", [], {}, "u")
    await queue.enqueue("b", [], {}, "u")
    await queue.update_status(id1, JobStatus.RUNNING)

    pending = await queue.list_jobs(status_filter=JobStatus.PENDING)
    running = await queue.list_jobs(status_filter=JobStatus.RUNNING)
    assert len(pending) == 1
    assert len(running) == 1


@pytest.mark.asyncio
async def test_list_jobs_pagination(queue: JobQueue):
    """list_jobs should respect limit and offset."""
    for i in range(5):
        await queue.enqueue(f"op{i}", [], {}, "u")

    page = await queue.list_jobs(limit=2, offset=0)
    assert len(page) == 2

    page2 = await queue.list_jobs(limit=2, offset=2)
    assert len(page2) == 2

    page3 = await queue.list_jobs(limit=2, offset=4)
    assert len(page3) == 1
