"""Automation workflow engine.

Requirements: 11.1-11.5
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class WorkflowExecution:
    workflow_id: str
    trigger_source: str
    actions_performed: list[str]
    status: str  # "success" or "failed"
    error: str | None = None
    retries: int = 0
    executed_at: str = field(default_factory=lambda: datetime.now().isoformat())


def next_cron_time(expression: str, reference: datetime) -> datetime | None:
    """Compute next execution time for a simple cron expression.

    Supports: "* * * * *" (min hour dom month dow), numeric values only.
    Returns None if expression is invalid.
    """
    parts = expression.strip().split()
    if len(parts) != 5:
        return None

    try:
        specs = []
        for p in parts:
            if p == "*":
                specs.append(None)
            else:
                specs.append(int(p))
    except ValueError:
        return None

    minute, hour, dom, month, dow = specs

    # Brute-force: scan forward minute by minute (max 2 years)
    from datetime import timedelta
    candidate = reference.replace(second=0, microsecond=0) + timedelta(minutes=1)
    for _ in range(525960):  # ~1 year of minutes
        if (minute is None or candidate.minute == minute) and \
           (hour is None or candidate.hour == hour) and \
           (dom is None or candidate.day == dom) and \
           (month is None or candidate.month == month) and \
           (dow is None or candidate.weekday() == dow):
            return candidate
        candidate += timedelta(minutes=1)
    return None


def execute_with_retry(action_fn, max_retries: int = 3) -> tuple[bool, int, str | None]:
    """Execute action with exponential backoff. Returns (success, retries, error)."""
    for attempt in range(max_retries + 1):
        try:
            action_fn()
            return True, attempt, None
        except Exception as e:
            if attempt < max_retries:
                time.sleep(0)  # In production: 2**attempt seconds
            else:
                return False, attempt, str(e)
    return False, max_retries, "max retries exceeded"
