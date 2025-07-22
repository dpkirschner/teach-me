"""API request/response schemas for jobs."""

from datetime import datetime
from uuid import UUID
from pydantic import BaseModel


class JobRequest(BaseModel):
    """Request schema for creating a job."""
    content: str


class JobResponse(BaseModel):
    """Response schema for job operations."""
    id: UUID
    created_at: datetime