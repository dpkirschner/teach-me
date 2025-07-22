"""Tests for Job API schemas."""

from datetime import datetime
from uuid import uuid4

import pytest

from teach_me.schemas.job import JobRequest, JobResponse


@pytest.mark.unit
class TestJobSchemas:
    """Test cases for Job API schemas."""

    def test_job_request_valid(self):
        """Test JobRequest with valid data."""
        job_request = JobRequest(content="Request content")

        assert job_request.content == "Request content"

    def test_job_request_empty_content(self):
        """Test JobRequest with empty content."""
        # Empty strings are allowed by default in Pydantic
        job_request = JobRequest(content="")
        assert job_request.content == ""

    def test_job_response_valid(self):
        """Test JobResponse with valid data."""
        job_id = uuid4()
        created_at = datetime.now()

        job_response = JobResponse(id=job_id, content="Test content", created_at=created_at)

        assert job_response.id == job_id
        assert job_response.content == "Test content"
        assert job_response.created_at == created_at

    def test_job_response_serialization(self):
        """Test JobResponse JSON serialization."""
        job_id = uuid4()
        created_at = datetime.now()

        job_response = JobResponse(id=job_id, content="Test content", created_at=created_at)

        json_data = job_response.model_dump()

        assert json_data["id"] == job_id
        assert json_data["content"] == "Test content"
        assert json_data["created_at"] == created_at
