"""Tests for the Job Queue REST API endpoints."""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import fakeredis.aioredis
import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app, _get_redis
from app.queue import JobQueue
from shared.models.jobs import JobPriority, JobStatus


@pytest.fixture
def fake_redis():
    """Create a fresh fakeredis async client for each test."""
    return fakeredis.aioredis.FakeRedis(decode_responses=True)


@pytest.fixture
def override_redis(fake_redis):
    """Override the FastAPI Redis dependency with fakeredis."""

    async def _override():
        return fake_redis

    app.dependency_overrides[_get_redis] = _override
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def queue(fake_redis):
    """A JobQueue backed by fakeredis for seeding test data."""
    return JobQueue(fake_redis)


@pytest.fixture
def client(override_redis):
    """Async HTTP client wired to the FastAPI app."""
    transport = ASGITransport(app=app)
    return AsyncClient(transport=transport, base_url="http://test")


# ------------------------------------------------------------------
# GET /jobs
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_jobs_empty(client):
    async with client:
        resp = await client.get("/jobs")
    assert resp.status_code == 200
    body = resp.json()
    assert body["jobs"] == []
    assert body["total"] == 0


@pytest.mark.asyncio
async def test_list_jobs_returns_seeded_jobs(client, queue):
    await queue.enqueue("pdf_merge", ["/a.pdf"], {}, "user1")
    await queue.enqueue("image_convert", ["/b.png"], {}, "user2")

    async with client:
        resp = await client.get("/jobs")
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2
    assert len(body["jobs"]) == 2


@pytest.mark.asyncio
async def test_list_jobs_filter_by_status(client, queue):
    job_id = await queue.enqueue("pdf_merge", ["/a.pdf"], {}, "user1")
    await queue.enqueue("image_convert", ["/b.png"], {}, "user2")
    # Move first job to running
    await queue.update_status(job_id, JobStatus.RUNNING)

    async with client:
        resp = await client.get("/jobs", params={"status": "running"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["jobs"][0]["id"] == job_id


@pytest.mark.asyncio
async def test_list_jobs_invalid_status(client):
    async with client:
        resp = await client.get("/jobs", params={"status": "bogus"})
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_list_jobs_pagination(client, queue):
    for i in range(5):
        await queue.enqueue("type", [f"/{i}.pdf"], {}, "user1")

    async with client:
        resp = await client.get("/jobs", params={"limit": 2, "offset": 0})
    assert resp.status_code == 200
    body = resp.json()
    assert len(body["jobs"]) == 2
    assert body["limit"] == 2
    assert body["offset"] == 0


# ------------------------------------------------------------------
# GET /jobs/{job_id}
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_job_found(client, queue):
    job_id = await queue.enqueue("pdf_merge", ["/a.pdf"], {}, "user1")

    async with client:
        resp = await client.get(f"/jobs/{job_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["job"]["id"] == job_id
    assert body["job"]["status"] == "pending"


@pytest.mark.asyncio
async def test_get_job_not_found(client):
    async with client:
        resp = await client.get("/jobs/nonexistent-id")
    assert resp.status_code == 404


# ------------------------------------------------------------------
# DELETE /jobs/{job_id}
# ------------------------------------------------------------------


@pytest.mark.asyncio
async def test_cancel_pending_job(client, queue):
    job_id = await queue.enqueue("pdf_merge", ["/a.pdf"], {}, "user1")

    async with client:
        resp = await client.delete(f"/jobs/{job_id}")
    assert resp.status_code == 200
    body = resp.json()
    assert body["job"]["status"] == "cancelled"
    assert body["message"] == "Job cancelled successfully"


@pytest.mark.asyncio
async def test_cancel_not_found(client):
    async with client:
        resp = await client.delete("/jobs/nonexistent-id")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_cancel_running_job_returns_409(client, queue):
    job_id = await queue.enqueue("pdf_merge", ["/a.pdf"], {}, "user1")
    await queue.update_status(job_id, JobStatus.RUNNING)

    async with client:
        resp = await client.delete(f"/jobs/{job_id}")
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_cancel_completed_job_returns_409(client, queue):
    job_id = await queue.enqueue("pdf_merge", ["/a.pdf"], {}, "user1")
    await queue.update_status(job_id, JobStatus.COMPLETED, output_file="/out.pdf")

    async with client:
        resp = await client.delete(f"/jobs/{job_id}")
    assert resp.status_code == 409
