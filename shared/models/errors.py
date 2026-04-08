"""API error response model."""

from pydantic import BaseModel


class APIError(BaseModel):
    error: str
    message: str
    field: str | None
    details: dict | None
