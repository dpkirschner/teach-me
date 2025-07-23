"""Business logic model for jobs."""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict


class JobModel(BaseModel):
    """Business logic model representing a job record."""

    id: UUID
    content: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
