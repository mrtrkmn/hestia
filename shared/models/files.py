"""File processing request/response models."""

from pydantic import BaseModel

from .jobs import JobStatus


class FileProcessRequest(BaseModel):
    operation: str
    source_format: str
    target_format: str | None
    parameters: dict
    file_ids: list[str]


class FileProcessResponse(BaseModel):
    job_id: str
    status: JobStatus
    message: str
