"""Tests for Job Pydantic models."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from teach_me.api.models.job import JobRequest, JobUpdateRequest
from teach_me.services.models.job import JobModel


@pytest.mark.unit
class TestJobModels:
    """Test cases for Job models."""

    def test_job_request_valid(self):
        """Test JobRequest with valid data."""
        job_request = JobRequest(content="Test job content")

        assert job_request.content == "Test job content"

    def test_job_request_empty_content(self):
        """Test JobRequest with empty content."""
        # Empty strings are allowed by default in Pydantic
        job_request = JobRequest(content="")
        assert job_request.content == ""

    def test_job_request_none_content(self):
        """Test JobRequest with None content."""
        with pytest.raises(ValidationError):
            JobRequest(content=None)

    def test_job_update_request_valid(self):
        """Test JobUpdateRequest with valid data."""
        job_update = JobUpdateRequest(content="Updated content")

        assert job_update.content == "Updated content"

    def test_job_update_request_optional_content(self):
        """Test JobUpdateRequest with no content (optional)."""
        job_update = JobUpdateRequest()

        assert job_update.content is None

    def test_job_update_request_exclude_unset(self):
        """Test JobUpdateRequest exclude_unset functionality."""
        job_update = JobUpdateRequest()
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
