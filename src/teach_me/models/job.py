"""Database model for jobs table."""

from datetime import datetime
from uuid import UUID
from typing import Optional
from pydantic import BaseModel


class JobModel(BaseModel):
    """Database model representing a job record."""
    
    id: UUID
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


class JobCreate(BaseModel):
    """Model for creating a new job record."""
    content: str


class JobUpdate(BaseModel):
    """Model for updating an existing job record."""
    content: Optional[str] = None