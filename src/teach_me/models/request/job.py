"""Database model for jobs table."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JobModel(BaseModel):
    """Database model representing a job record."""

    id: UUID
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class JobCreate(BaseModel):
    """Model for creating a new job record."""

    content: str


class JobUpdate(BaseModel):
    """Model for updating an existing job record."""

    content: str | None = None
