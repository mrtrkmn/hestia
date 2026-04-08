"""Property test: Job ID uniqueness.

**Validates: Requirements 13.2**

For any set of submitted jobs, all assigned job IDs should be unique
(no two jobs share the same ID).
"""

import os
import sys

import fakeredis.aioredis
import pytest
import pytest_asyncio
from hypothesis import given, settings
from hypothesis import strategies as st

# Add job-queue directory to path so we can import app.queue
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.queue import JobQueue
from shared.models.jobs import JobPriority

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

job_type_st = st.sampled_from(["pdf_merge", "pdf_split", "image_convert", "video_transcode", "audio_transcode"])
priority_st = st.sampled_from(list(JobPriority))
user_id_st = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N")),
    min_size=1,
    max_size=20,
)
file_path_st = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P")),
    min_size=1,
    max_size=50,
).map(lambda s: f"/{s}")

job_params_st = st.fixed_dictionaries({}, optional={"format": st.sampled_from(["png", "jpeg", "pdf", "mp4"])})

batch_size_st = st.integers(min_value=1, max_value=50)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest_asyncio.fixture
async def redis_client():
    client = fakeredis.aioredis.FakeRedis(decode_responses=False)
    yield client
    await client.flushall()
    await client.aclose()


# ---------------------------------------------------------------------------
# Property 22: Job ID uniqueness
# ---------------------------------------------------------------------------

@settings(max_examples=50, deadline=None)
@given(data=st.data())
@pytest.mark.asyncio
async def test_job_id_uniqueness(data: st.DataObject) -> None:
    """**Validates: Requirements 13.2**

    Generate batches of jobs and verify all assigned IDs are unique.
    """
    client = fakeredis.aioredis.FakeRedis(decode_responses=False)
    queue = JobQueue(client)

    batch_size = data.draw(batch_size_st, label="batch_size")

    job_ids: list[str] = []
    for _ in range(batch_size):
        job_type = data.draw(job_type_st, label="job_type")
        priority = data.draw(priority_st, label="priority")
        user_id = data.draw(user_id_st, label="user_id")
        input_files = data.draw(
            st.lists(file_path_st, min_size=1, max_size=5), label="input_files"
        )
        params = data.draw(job_params_st, label="params")

        job_id = await queue.enqueue(
            type=job_type,
            input_files=input_files,
            parameters=params,
            user_id=user_id,
            priority=priority,
        )
        job_ids.append(job_id)

    # All IDs must be unique
    assert len(job_ids) == len(set(job_ids)), (
        f"Duplicate job IDs found in batch of {batch_size}: "
        f"{[jid for jid in job_ids if job_ids.count(jid) > 1]}"
    )

    await client.flushall()
    await client.aclose()
