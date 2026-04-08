"""Property test: Job queue FIFO ordering with priority.

**Validates: Requirements 13.3**

For any sequence of jobs, jobs with higher priority should be dispatched
before jobs with lower priority. Within the same priority level, jobs
should be dispatched in submission order (FIFO).
"""

import os
import sys

import fakeredis.aioredis
import pytest
from hypothesis import given, settings
from hypothesis import strategies as st

# Add job-queue directory to path so we can import app.queue
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from app.queue import JobQueue
from shared.models.jobs import JobPriority

# ---------------------------------------------------------------------------
# Strategies
# ---------------------------------------------------------------------------

priority_st = st.sampled_from([JobPriority.HIGH, JobPriority.NORMAL, JobPriority.LOW])

job_spec_st = st.fixed_dictionaries(
    {
        "priority": priority_st,
        "type": st.sampled_from(["pdf_merge", "pdf_split", "image_convert", "video_transcode"]),
        "user_id": st.text(
            alphabet=st.characters(whitelist_categories=("L", "N")),
            min_size=1,
            max_size=10,
        ),
    }
)

# Generate non-empty lists of job specs (1–30 jobs)
job_sequence_st = st.lists(job_spec_st, min_size=1, max_size=30)

# Priority rank: lower number = higher priority (dispatched first)
_PRIORITY_RANK = {
    JobPriority.HIGH: 0,
    JobPriority.NORMAL: 1,
    JobPriority.LOW: 2,
}


# ---------------------------------------------------------------------------
# Property 23: Job queue FIFO ordering with priority
# ---------------------------------------------------------------------------

@settings(max_examples=50, deadline=None)
@given(jobs=job_sequence_st)
@pytest.mark.asyncio
async def test_fifo_ordering_with_priority(jobs: list[dict]) -> None:
    """**Validates: Requirements 13.3**

    Generate sequences of jobs with varying priorities and verify dispatch
    order: higher priority first, FIFO within same priority.
    """
    client = fakeredis.aioredis.FakeRedis(decode_responses=False)
    queue = JobQueue(client)

    # Enqueue all jobs and record (job_id, priority, submission_index)
    enqueued: list[tuple[str, JobPriority, int]] = []
    for idx, spec in enumerate(jobs):
        job_id = await queue.enqueue(
            type=spec["type"],
            input_files=[f"/file_{idx}.dat"],
            parameters={},
            user_id=spec["user_id"],
            priority=spec["priority"],
        )
        enqueued.append((job_id, spec["priority"], idx))

    # Dequeue all jobs and record the order
    dequeued_ids: list[str] = []
    while True:
        job = await queue.dequeue()
        if job is None:
            break
        dequeued_ids.append(job.id)

    # All enqueued jobs should be dequeued
    assert len(dequeued_ids) == len(enqueued), (
        f"Expected {len(enqueued)} dequeued jobs, got {len(dequeued_ids)}"
    )

    # Build a lookup: job_id -> (priority, submission_index)
    id_to_info = {jid: (pri, idx) for jid, pri, idx in enqueued}

    # Verify ordering constraints
    for i in range(len(dequeued_ids)):
        for j in range(i + 1, len(dequeued_ids)):
            pri_i, idx_i = id_to_info[dequeued_ids[i]]
            pri_j, idx_j = id_to_info[dequeued_ids[j]]

            rank_i = _PRIORITY_RANK[pri_i]
            rank_j = _PRIORITY_RANK[pri_j]

            # Higher priority (lower rank) must come first
            assert rank_i <= rank_j, (
                f"Job at dequeue position {i} has priority {pri_i.value} "
                f"(rank {rank_i}) but job at position {j} has priority "
                f"{pri_j.value} (rank {rank_j}) — higher priority should "
                f"be dispatched first"
            )

            # Within same priority, FIFO order (earlier submission first)
            if rank_i == rank_j:
                assert idx_i < idx_j, (
                    f"Jobs at dequeue positions {i} and {j} have same "
                    f"priority {pri_i.value} but submission order is "
                    f"violated: index {idx_i} should come before {idx_j}"
                )

    await client.flushall()
    await client.aclose()
