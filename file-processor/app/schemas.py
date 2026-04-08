"""File Processor schemas."""

from pydantic import BaseModel


class ProcessRequest(BaseModel):
    operation: str
    source_format: str
    target_format: str | None = None
    parameters: dict = {}
    file_ids: list[str] = []


class ProcessResponse(BaseModel):
    job_id: str
    status: str
    message: str


class ErrorResponse(BaseModel):
    filename: str
    reason: str
