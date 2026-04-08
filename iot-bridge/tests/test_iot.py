"""Property tests for IoT Bridge.

Property 18: MQTT topic pattern matching
Property 19: Cron expression scheduling
Property 20: Automation workflow execution logging

Validates: Requirements 11.1, 11.3, 11.4
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from datetime import datetime
from hypothesis import given, settings
from hypothesis import strategies as st

from app.mqtt import mqtt_topic_matches
from app.automations import next_cron_time, WorkflowExecution


# ---------------------------------------------------------------------------
# Property 18: MQTT topic pattern matching
# Feature: hestia, Property 18: MQTT topic pattern matching
# ---------------------------------------------------------------------------

_MATCH_CASES = [
    ("home/+/temperature", "home/living/temperature", True),
    ("home/+/temperature", "home/bedroom/temperature", True),
    ("home/+/temperature", "home/living/humidity", False),
    ("home/#", "home/living/temperature", True),
    ("home/#", "home", True),
    ("sensor/data", "sensor/data", True),
    ("sensor/data", "sensor/other", False),
    ("+/+/status", "home/light/status", True),
    ("+/+/status", "home/light/brightness", False),
]


@given(case=st.sampled_from(_MATCH_CASES))
@settings(max_examples=50)
def test_mqtt_topic_matching(case):
    pattern, topic, expected = case
    assert mqtt_topic_matches(pattern, topic) == expected


# Exact match: topic should always match itself
@given(topic=st.from_regex(r"[a-z]{1,5}(/[a-z]{1,5}){0,3}", fullmatch=True))
@settings(max_examples=100)
def test_exact_topic_matches_itself(topic: str):
    assert mqtt_topic_matches(topic, topic) is True


# '#' at end matches everything under prefix
@given(
    prefix=st.from_regex(r"[a-z]{1,5}", fullmatch=True),
    suffix=st.from_regex(r"(/[a-z]{1,5}){0,3}", fullmatch=True),
)
@settings(max_examples=100)
def test_hash_wildcard_matches_subtree(prefix: str, suffix: str):
    assert mqtt_topic_matches(f"{prefix}/#", f"{prefix}{suffix}") is True


# ---------------------------------------------------------------------------
# Property 19: Cron expression scheduling
# Feature: hestia, Property 19: Cron expression scheduling
# ---------------------------------------------------------------------------

@given(minute=st.integers(min_value=0, max_value=59))
@settings(max_examples=60)
def test_cron_specific_minute(minute: int):
    ref = datetime(2025, 1, 1, 0, 0, 0)
    result = next_cron_time(f"{minute} * * * *", ref)
    assert result is not None
    assert result.minute == minute
    assert result > ref


@given(hour=st.integers(min_value=0, max_value=23))
@settings(max_examples=24)
def test_cron_specific_hour(hour: int):
    ref = datetime(2025, 1, 1, 0, 0, 0)
    result = next_cron_time(f"0 {hour} * * *", ref)
    assert result is not None
    assert result.hour == hour


def test_cron_wildcard_runs_next_minute():
    ref = datetime(2025, 6, 15, 12, 30, 0)
    result = next_cron_time("* * * * *", ref)
    assert result is not None
    assert result.minute == 31


# ---------------------------------------------------------------------------
# Property 20: Automation workflow execution logging
# Feature: hestia, Property 20: Automation workflow execution logging
# ---------------------------------------------------------------------------

@given(
    workflow_id=st.text(min_size=1, max_size=10),
    trigger=st.text(min_size=1, max_size=20),
    actions=st.lists(st.text(min_size=1, max_size=10), min_size=1, max_size=5),
    status=st.sampled_from(["success", "failed"]),
)
@settings(max_examples=100)
def test_execution_log_contains_required_fields(
    workflow_id: str, trigger: str, actions: list[str], status: str
):
    log = WorkflowExecution(
        workflow_id=workflow_id,
        trigger_source=trigger,
        actions_performed=actions,
        status=status,
    )
    assert log.executed_at  # timestamp present
    assert log.trigger_source == trigger
    assert log.actions_performed == actions
    assert log.status in ("success", "failed")
