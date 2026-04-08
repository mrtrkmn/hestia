"""Automation workflow data models."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel


class TriggerType(str, Enum):
    MQTT = "mqtt"
    CRON = "cron"


class WorkflowTrigger(BaseModel):
    type: TriggerType
    mqtt_topic: str | None
    cron_expression: str | None


class WorkflowAction(BaseModel):
    type: str
    parameters: dict


class AutomationWorkflow(BaseModel):
    id: str
    name: str
    trigger: WorkflowTrigger
    actions: list[WorkflowAction]
    enabled: bool
    created_by: str
    created_at: datetime


class WorkflowExecution(BaseModel):
    id: str
    workflow_id: str
    trigger_source: str
    actions_performed: list[str]
    status: str
    error: str | None
    retries: int
    executed_at: datetime
