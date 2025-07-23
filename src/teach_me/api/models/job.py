"""API request/response schemas for jobs."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class JobRequest(BaseModel):
    """Request schema for creating a job."""

    content: str


class JobUpdateRequest(BaseModel):
    """Request schema for updating a job."""

    content: str | None = None


class JobResponse(BaseModel):
    """Response schema for job operations."""

    id: UUID
    content: str
    created_at: datetime
