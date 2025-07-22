"""Tests for Job Pydantic models."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from src.teach_me.models.job import JobCreate, JobModel, JobUpdate


@pytest.mark.unit
class TestJobModels:
    """Test cases for Job models."""

    def test_job_create_valid(self):
        """Test JobCreate with valid data."""
        job_create = JobCreate(content="Test job content")

        assert job_create.content == "Test job content"

    def test_job_create_empty_content(self):
        """Test JobCreate with empty content."""
        # Empty strings are allowed by default in Pydantic
        job_create = JobCreate(content="")
        assert job_create.content == ""

    def test_job_create_none_content(self):
        """Test JobCreate with None content."""
        with pytest.raises(ValidationError):
            JobCreate(content=None)

    def test_job_update_valid(self):
        """Test JobUpdate with valid data."""
        job_update = JobUpdate(content="Updated content")

        assert job_update.content == "Updated content"

    def test_job_update_optional_content(self):
        """Test JobUpdate with no content (optional)."""
        job_update = JobUpdate()

        assert job_update.content is None

    def test_job_update_exclude_unset(self):
        """Test JobUpdate exclude_unset functionality."""
        job_update = JobUpdate()
        data = job_update.model_dump(exclude_unset=True)

        assert "content" not in data

    def test_job_model_valid(self):
        """Test JobModel with valid data."""
        job_id = uuid4()
        created_at = datetime.now()

        job_model = JobModel(id=job_id, content="Test content", created_at=created_at)

        assert job_model.id == job_id
        assert job_model.content == "Test content"
        assert job_model.created_at == created_at

    def test_job_model_invalid_uuid(self):
        """Test JobModel with invalid UUID."""
        with pytest.raises(ValidationError):
            JobModel(id="invalid-uuid", content="Test content", created_at=datetime.now())

    def test_job_model_from_dict(self):
        """Test JobModel creation from dictionary."""
        job_id = uuid4()
        created_at = datetime.now()

        data = {
            "id": str(job_id),
            "content": "Test content",
            "created_at": created_at.isoformat(),
        }

        job_model = JobModel(**data)

        assert job_model.id == job_id
        assert job_model.content == "Test content"
