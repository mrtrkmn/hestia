"""Property test: API model JSON round-trip.

**Validates: Requirements 17.5, 17.6**

For any valid API request or response object, serializing it to JSON
and then deserializing the JSON back should produce an equivalent object.
"""

from datetime import datetime, timezone

from hypothesis import given, settings
from hypothesis import strategies as st

from shared.models.auth import AuthToken, User, UserRole
from shared.models.automation import (
    AutomationWorkflow,
    TriggerType,
    WorkflowAction,
    WorkflowExecution,
    WorkflowTrigger,
)
from shared.models.errors import APIError
from shared.models.files import FileProcessRequest, FileProcessResponse
from shared.models.health import ServiceHealth, ServiceStatus
from shared.models.jobs import Job, JobPriority, JobStatus
from shared.models.pipelines import Pipeline, PipelineStep
from shared.models.storage import ShareProtocol, StorageShare

# ---------------------------------------------------------------------------
# Reusable strategies
# ---------------------------------------------------------------------------

safe_text = st.text(
    alphabet=st.characters(whitelist_categories=("L", "N", "P", "Z")),
    min_size=1,
    max_size=50,
)

safe_dict = st.dictionaries(safe_text, safe_text, max_size=3)

aware_datetimes = st.datetimes(
    min_value=datetime(2000, 1, 1),
    max_value=datetime(2099, 12, 31),
    timezones=st.just(timezone.utc),
)


# ---------------------------------------------------------------------------
# Model strategies
# ---------------------------------------------------------------------------

job_status_st = st.sampled_from(list(JobStatus))
job_priority_st = st.sampled_from(list(JobPriority))
user_role_st = st.sampled_from(list(UserRole))
share_protocol_st = st.sampled_from(list(ShareProtocol))
trigger_type_st = st.sampled_from(list(TriggerType))
service_status_st = st.sampled_from(list(ServiceStatus))


api_error_st = st.builds(
    APIError,
    error=safe_text,
    message=safe_text,
    field=st.one_of(st.none(), safe_text),
    details=st.one_of(st.none(), safe_dict),
)

auth_token_st = st.builds(
    AuthToken,
    access_token=safe_text,
    token_type=safe_text,
    expires_in=st.integers(min_value=0, max_value=86400),
)

pipeline_step_st = st.builds(
    PipelineStep,
    operation=safe_text,
    parameters=safe_dict,
)

pipeline_st = st.builds(
    Pipeline,
    id=safe_text,
    name=safe_text,
    steps=st.lists(pipeline_step_st, min_size=0, max_size=5),
    created_by=safe_text,
    created_at=aware_datetimes,
)

file_process_request_st = st.builds(
    FileProcessRequest,
    operation=safe_text,
    source_format=safe_text,
    target_format=st.one_of(st.none(), safe_text),
    parameters=safe_dict,
    file_ids=st.lists(safe_text, min_size=0, max_size=5),
)

file_process_response_st = st.builds(
    FileProcessResponse,
    job_id=safe_text,
    status=job_status_st,
    message=safe_text,
)


user_st = st.builds(
    User,
    id=safe_text,
    username=safe_text,
    email=safe_text,
    role=user_role_st,
    totp_enabled=st.booleans(),
    locked_until=st.one_of(st.none(), aware_datetimes),
    failed_attempts=st.integers(min_value=0, max_value=100),
    created_at=aware_datetimes,
)

storage_share_st = st.builds(
    StorageShare,
    id=safe_text,
    name=safe_text,
    path=safe_text,
    protocols=st.lists(share_protocol_st, min_size=1, max_size=2),
    zfs_dataset=st.one_of(st.none(), safe_text),
    allowed_users=st.lists(safe_text, min_size=0, max_size=5),
    read_only=st.booleans(),
    created_at=aware_datetimes,
)

workflow_trigger_st = st.builds(
    WorkflowTrigger,
    type=trigger_type_st,
    mqtt_topic=st.one_of(st.none(), safe_text),
    cron_expression=st.one_of(st.none(), safe_text),
)

workflow_action_st = st.builds(
    WorkflowAction,
    type=safe_text,
    parameters=safe_dict,
)

automation_workflow_st = st.builds(
    AutomationWorkflow,
    id=safe_text,
    name=safe_text,
    trigger=workflow_trigger_st,
    actions=st.lists(workflow_action_st, min_size=0, max_size=5),
    enabled=st.booleans(),
    created_by=safe_text,
    created_at=aware_datetimes,
)

workflow_execution_st = st.builds(
    WorkflowExecution,
    id=safe_text,
    workflow_id=safe_text,
    trigger_source=safe_text,
    actions_performed=st.lists(safe_text, min_size=0, max_size=5),
    status=safe_text,
    error=st.one_of(st.none(), safe_text),
    retries=st.integers(min_value=0, max_value=10),
    executed_at=aware_datetimes,
)

service_health_st = st.builds(
    ServiceHealth,
    name=safe_text,
    status=service_status_st,
    uptime_seconds=st.integers(min_value=0, max_value=10_000_000),
    last_check=aware_datetimes,
    details=st.one_of(st.none(), safe_dict),
)

job_st = st.builds(
    Job,
    id=safe_text,
    type=safe_text,
    status=job_status_st,
    priority=job_priority_st,
    input_files=st.lists(safe_text, min_size=0, max_size=5),
    output_file=st.one_of(st.none(), safe_text),
    parameters=safe_dict,
    progress=st.integers(min_value=0, max_value=100),
    error=st.one_of(st.none(), safe_text),
    retries=st.integers(min_value=0, max_value=10),
    created_at=aware_datetimes,
    updated_at=aware_datetimes,
    completed_at=st.one_of(st.none(), aware_datetimes),
    user_id=safe_text,
)


# ---------------------------------------------------------------------------
# Property 30: API model JSON round-trip
# ---------------------------------------------------------------------------

COMMON_SETTINGS = settings(max_examples=50, deadline=None)


@COMMON_SETTINGS
@given(instance=api_error_st)
def test_api_error_roundtrip(instance: APIError) -> None:
    """**Validates: Requirements 17.5, 17.6**"""
    json_str = instance.model_dump_json()
    restored = APIError.model_validate_json(json_str)
    assert restored == instance


@COMMON_SETTINGS
@given(instance=auth_token_st)
def test_auth_token_roundtrip(instance: AuthToken) -> None:
    """**Validates: Requirements 17.5, 17.6**"""
    json_str = instance.model_dump_json()
    restored = AuthToken.model_validate_json(json_str)
    assert restored == instance


@COMMON_SETTINGS
@given(instance=pipeline_step_st)
def test_pipeline_step_roundtrip(instance: PipelineStep) -> None:
    """**Validates: Requirements 17.5, 17.6**"""
    json_str = instance.model_dump_json()
    restored = PipelineStep.model_validate_json(json_str)
    assert restored == instance


@COMMON_SETTINGS
@given(instance=pipeline_st)
def test_pipeline_roundtrip(instance: Pipeline) -> None:
    """**Validates: Requirements 17.5, 17.6**"""
    json_str = instance.model_dump_json()
    restored = Pipeline.model_validate_json(json_str)
    assert restored == instance


@COMMON_SETTINGS
@given(instance=file_process_request_st)
def test_file_process_request_roundtrip(instance: FileProcessRequest) -> None:
    """**Validates: Requirements 17.5, 17.6**"""
    json_str = instance.model_dump_json()
    restored = FileProcessRequest.model_validate_json(json_str)
    assert restored == instance


@COMMON_SETTINGS
@given(instance=file_process_response_st)
def test_file_process_response_roundtrip(instance: FileProcessResponse) -> None:
    """**Validates: Requirements 17.5, 17.6**"""
    json_str = instance.model_dump_json()
    restored = FileProcessResponse.model_validate_json(json_str)
    assert restored == instance


@COMMON_SETTINGS
@given(instance=user_st)
def test_user_roundtrip(instance: User) -> None:
    """**Validates: Requirements 17.5, 17.6**"""
    json_str = instance.model_dump_json()
    restored = User.model_validate_json(json_str)
    assert restored == instance


@COMMON_SETTINGS
@given(instance=storage_share_st)
def test_storage_share_roundtrip(instance: StorageShare) -> None:
    """**Validates: Requirements 17.5, 17.6**"""
    json_str = instance.model_dump_json()
    restored = StorageShare.model_validate_json(json_str)
    assert restored == instance


@COMMON_SETTINGS
@given(instance=workflow_trigger_st)
def test_workflow_trigger_roundtrip(instance: WorkflowTrigger) -> None:
    """**Validates: Requirements 17.5, 17.6**"""
    json_str = instance.model_dump_json()
    restored = WorkflowTrigger.model_validate_json(json_str)
    assert restored == instance


@COMMON_SETTINGS
@given(instance=workflow_action_st)
def test_workflow_action_roundtrip(instance: WorkflowAction) -> None:
    """**Validates: Requirements 17.5, 17.6**"""
    json_str = instance.model_dump_json()
    restored = WorkflowAction.model_validate_json(json_str)
    assert restored == instance


@COMMON_SETTINGS
@given(instance=automation_workflow_st)
def test_automation_workflow_roundtrip(instance: AutomationWorkflow) -> None:
    """**Validates: Requirements 17.5, 17.6**"""
    json_str = instance.model_dump_json()
    restored = AutomationWorkflow.model_validate_json(json_str)
    assert restored == instance


@COMMON_SETTINGS
@given(instance=workflow_execution_st)
def test_workflow_execution_roundtrip(instance: WorkflowExecution) -> None:
    """**Validates: Requirements 17.5, 17.6**"""
    json_str = instance.model_dump_json()
    restored = WorkflowExecution.model_validate_json(json_str)
    assert restored == instance


@COMMON_SETTINGS
@given(instance=service_health_st)
def test_service_health_roundtrip(instance: ServiceHealth) -> None:
    """**Validates: Requirements 17.5, 17.6**"""
    json_str = instance.model_dump_json()
    restored = ServiceHealth.model_validate_json(json_str)
    assert restored == instance


@COMMON_SETTINGS
@given(instance=job_st)
def test_job_roundtrip(instance: Job) -> None:
    """**Validates: Requirements 17.5, 17.6**"""
    json_str = instance.model_dump_json()
    restored = Job.model_validate_json(json_str)
    assert restored == instance
