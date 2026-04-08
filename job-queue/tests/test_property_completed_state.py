"""Property test: Completed job state invariant.

**Validates: Requirements 13.5**

For any job that completes successfully, querying its status should return
"completed" with a non-null output file reference, progress == 100, and
completed_at is not None.
"""

import os
import sys

import fakeredis.aioredis
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.queue import JobQueue
from shared.models.jobs import JobPriority, JobStatus

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

job_type_st = st.sampled_from([
    "pdf_merge", "pdf_split", "pdf_ocr", "pdf_compress",
    "image_convert", "video_transcode", "audio_transcode",
])

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

job_params_st = st.fixed_dictionaries(
    {},
    optional={"format": st.sampled_from(["png", "jpeg", "pdf", "mp4", "mp3"])},
)

output_file_st = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P")),
    min_size=1,
    max_size=80,
).map(lambda s: f"/output/{s}")


# ---------------------------------------------------------------------------
# Property 24: Completed job state invariant
# ---------------------------------------------------------------------------

@settings(max_examples=50, deadline=None)
@given(data=st.data())
@pytest.mark.asyncio
async def test_completed_job_state_invariant(data: st.DataObject) -> None:
    """**Validates: Requirements 13.5**

    For any job that completes successfully, verify status is "completed",
    output_file is non-null, progress == 100, and completed_at is not None.
    """
    client = fakeredis.aioredis.FakeRedis(decode_responses=False)
    queue = JobQueue(client)

    # Draw random job parameters
    job_type = data.draw(job_type_st, label="job_type")
    priority = data.draw(priority_st, label="priority")
    user_id = data.draw(user_id_st, label="user_id")
    input_files = data.draw(
        st.lists(file_path_st, min_size=1, max_size=5), label="input_files"
    )
    params = data.draw(job_params_st, label="params")
    output_file = data.draw(output_file_st, label="output_file")

    # Enqueue the job
    job_id = await queue.enqueue(
        type=job_type,
        input_files=input_files,
        parameters=params,
        user_id=user_id,
        priority=priority,
    )

    # Dequeue (transitions to RUNNING)
    running_job = await queue.dequeue()
    assert running_job is not None, "Expected to dequeue a job"
    assert running_job.id == job_id

    # Complete the job with a random output_file
    completed_job = await queue.update_status(
        job_id,
        JobStatus.COMPLETED,
        output_file=output_file,
    )

    # Verify the completed state invariant
    assert completed_job is not None, "update_status should return the job"
    assert completed_job.status == JobStatus.COMPLETED, (
        f"Expected status 'completed', got '{completed_job.status.value}'"
    )
    assert completed_job.output_file is not None, (
        "Completed job must have a non-null output_file"
    )
    assert completed_job.output_file == output_file, (
        f"Expected output_file '{output_file}', got '{completed_job.output_file}'"
    )
    assert completed_job.progress == 100, (
        f"Expected progress 100, got {completed_job.progress}"
    )
    assert completed_job.completed_at is not None, (
        "Completed job must have a non-null completed_at timestamp"
    )

    # Also verify via a fresh get_job query (round-trip through Redis)
    fetched_job = await queue.get_job(job_id)
    assert fetched_job is not None
    assert fetched_job.status == JobStatus.COMPLETED
    assert fetched_job.output_file == output_file
    assert fetched_job.progress == 100
    assert fetched_job.completed_at is not None

    await client.flushall()
    await client.aclose()
