"""Pipeline data models."""

from datetime import datetime

from pydantic import BaseModel


class PipelineStep(BaseModel):
    operation: str
    parameters: dict


class Pipeline(BaseModel):
    id: str
    name: str
    steps: list[PipelineStep]
    created_by: str
    created_at: datetime
