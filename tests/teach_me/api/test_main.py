"""Tests for the FastAPI endpoints."""

from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from teach_me.api.main import app, get_job_service
from teach_me.schemas.job import JobResponse


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_service(mocker):
    """Fixture to create a mock JobService."""
    return mocker.Mock()


@pytest.fixture
def client_with_mock_service(client, mock_service):
    """
    Yields a tuple of (TestClient, Mock) with the service dependency
    overridden and cleans up the override after the test.
    """
    app.dependency_overrides[get_job_service] = lambda: mock_service
    yield client, mock_service
    app.dependency_overrides.clear()


@pytest.mark.api
class TestJobAPI:
    """Test cases for Job API endpoints."""

    def test_create_job_success(self, client_with_mock_service):
        """Test successful job creation via API."""
        client, mock_service = client_with_mock_service
        job_content = "Test job content"
        job_id = uuid4()

        mock_service.create_job.return_value = JobResponse(
            id=job_id, content=job_content, created_at=datetime.now()
        )

        response = client.post("/jobs/", json={"content": job_content})

        assert response.status_code == 201
        data = response.json()
        assert data["content"] == job_content
        assert "id" in data
        mock_service.create_job.assert_called_once()

    def test_create_job_service_error(self, client_with_mock_service):
        """Test job creation when service raises error."""
        client, mock_service = client_with_mock_service
        mock_service.create_job.side_effect = Exception("Database error")

        response = client.post("/jobs/", json={"content": "Test job content"})

        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]

    def test_get_job_success(self, client_with_mock_service):
        """Test successful job retrieval via API."""
        client, mock_service = client_with_mock_service
        job_id = uuid4()
        mock_service.get_job_by_id.return_value = JobResponse(
            id=job_id, content="Test content", created_at=datetime.now()
        )

        response = client.get(f"/jobs/{job_id}")

        assert response.status_code == 200
        assert response.json()["id"] == str(job_id)
        mock_service.get_job_by_id.assert_called_once_with(job_id)

    def test_get_job_not_found(self, client_with_mock_service):
        """Test job retrieval when job not found."""
        client, mock_service = client_with_mock_service
        job_id = uuid4()
        mock_service.get_job_by_id.return_value = None

        response = client.get(f"/jobs/{job_id}")

        assert response.status_code == 404

    def test_get_jobs_success(self, client_with_mock_service):
        """Test successful retrieval of all jobs via API."""
        client, mock_service = client_with_mock_service
        mock_service.get_all_jobs.return_value = [
            JobResponse(id=uuid4(), content="Job 1", created_at=datetime.now()),
            JobResponse(id=uuid4(), content="Job 2", created_at=datetime.now()),
        ]

        response = client.get("/jobs/")

        assert response.status_code == 200
        assert len(response.json()) == 2
        mock_service.get_all_jobs.assert_called_once_with(offset=0, limit=100)

    def test_update_job_success(self, client_with_mock_service):
        """Test successful job update via API."""
        client, mock_service = client_with_mock_service
        job_id = uuid4()
        mock_service.update_job.return_value = JobResponse(
            id=job_id, content="Updated", created_at=datetime.now()
        )

        response = client.put(f"/jobs/{job_id}", json={"content": "Updated"})

        assert response.status_code == 200
        assert response.json()["content"] == "Updated"
        mock_service.update_job.assert_called_once()

    def test_delete_job_success(self, client_with_mock_service):
        """Test successful job deletion via API."""
        client, mock_service = client_with_mock_service
        job_id = uuid4()
        mock_service.delete_job.return_value = True

        response = client.delete(f"/jobs/{job_id}")

        assert response.status_code == 200
        assert response.json()["message"] == "Job deleted successfully"
        mock_service.delete_job.assert_called_once_with(job_id)

    # These tests do not need the mock DAO, so they use the original 'client' fixture
    def test_create_job_invalid_payload(self, client):
        """Test job creation with invalid payload."""
        response = client.post("/jobs/", json={"invalid_field": "value"})
        assert response.status_code == 422

    def test_get_job_invalid_uuid(self, client):
        """Test job retrieval with invalid UUID."""
        response = client.get("/jobs/invalid-uuid")
        assert response.status_code == 422
