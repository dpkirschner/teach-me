"""Pytest configuration and shared fixtures."""

from datetime import datetime
from unittest.mock import Mock
from uuid import uuid4

import pytest

from teach_me.api.models.job import JobRequest, JobUpdateRequest
from teach_me.dao.job_dao import JobDAO
from teach_me.services.models.job import JobModel


@pytest.fixture
def mock_supabase_client():
    """Mock Supabase client for testing."""
    mock_client = Mock()
    mock_table = Mock()
    mock_client.table.return_value = mock_table
    return mock_client


@pytest.fixture
def job_dao(mock_supabase_client):
    """JobDAO instance with mocked Supabase client."""
    return JobDAO(mock_supabase_client)


@pytest.fixture
def sample_job_create():
    """Sample JobRequest data for testing."""
    return JobRequest(content="Test job content")


@pytest.fixture
def sample_job_update():
    """Sample JobUpdateRequest data for testing."""
    return JobUpdateRequest(content="Updated job content")


@pytest.fixture
def sample_job_model():
    """Sample JobModel for testing."""
    return JobModel(id=uuid4(), content="Test job content", created_at=datetime.now())


@pytest.fixture
def mock_supabase_result():
    """Mock Supabase query result."""

    def _create_result(data=None, count=None):
        result = Mock()
        result.data = data or []
        result.count = count
        return result

    return _create_result
