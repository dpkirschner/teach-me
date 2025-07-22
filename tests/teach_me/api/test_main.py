"""Tests for the FastAPI endpoints."""

from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from teach_me.api.main import app, get_job_dao
from teach_me.models.request.job import JobModel


@pytest.fixture
def client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_dao(mocker):
    """Fixture to create a mock JobDAO."""
    return mocker.Mock()


@pytest.fixture
def client_with_mock_dao(client, mock_dao):
    """
    Yields a tuple of (TestClient, Mock) with the DAO dependency
    overridden and cleans up the override after the test.
    """
    app.dependency_overrides[get_job_dao] = lambda: mock_dao
    yield client, mock_dao
    app.dependency_overrides.clear()


@pytest.mark.api
class TestJobAPI:
    """Test cases for Job API endpoints."""

    def test_create_job_success(self, client_with_mock_dao):
        """Test successful job creation via API."""
        client, mock_dao = client_with_mock_dao
        job_content = "Test job content"

        mock_dao.create.return_value = JobModel(id=uuid4(), content=job_content, created_at=datetime.now())

        response = client.post("/jobs/", json={"content": job_content})

        assert response.status_code == 201
        data = response.json()
        assert data["content"] == job_content
        assert "id" in data
        mock_dao.create.assert_called_once()

    def test_create_job_dao_error(self, client_with_mock_dao):
        """Test job creation when DAO raises error."""
        client, mock_dao = client_with_mock_dao
        mock_dao.create.side_effect = Exception("Database error")

        response = client.post("/jobs/", json={"content": "Test job content"})

        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]

    def test_get_job_success(self, client_with_mock_dao):
        """Test successful job retrieval via API."""
        client, mock_dao = client_with_mock_dao
        job_id = uuid4()
        mock_dao.get_by_id.return_value = JobModel(
            id=job_id, content="Test content", created_at=datetime.now()
        )

        response = client.get(f"/jobs/{job_id}")

        assert response.status_code == 200
        assert response.json()["id"] == str(job_id)
        mock_dao.get_by_id.assert_called_once_with(job_id)

    def test_get_job_not_found(self, client_with_mock_dao):
        """Test job retrieval when job not found."""
        client, mock_dao = client_with_mock_dao
        job_id = uuid4()
        mock_dao.get_by_id.return_value = None

        response = client.get(f"/jobs/{job_id}")

        assert response.status_code == 404

    def test_get_jobs_success(self, client_with_mock_dao):
        """Test successful retrieval of all jobs via API."""
        client, mock_dao = client_with_mock_dao
        mock_dao.get_all.return_value = [
            JobModel(id=uuid4(), content="Job 1", created_at=datetime.now()),
            JobModel(id=uuid4(), content="Job 2", created_at=datetime.now()),
        ]

        response = client.get("/jobs/")

        assert response.status_code == 200
        assert len(response.json()) == 2
        mock_dao.get_all.assert_called_once_with(limit=100, offset=0)

    def test_update_job_success(self, client_with_mock_dao):
        """Test successful job update via API."""
        client, mock_dao = client_with_mock_dao
        job_id = uuid4()
        mock_dao.update.return_value = JobModel(id=job_id, content="Updated", created_at=datetime.now())

        response = client.put(f"/jobs/{job_id}", json={"content": "Updated"})

        assert response.status_code == 200
        assert response.json()["content"] == "Updated"
        mock_dao.update.assert_called_once()

    def test_delete_job_success(self, client_with_mock_dao):
        """Test successful job deletion via API."""
        client, mock_dao = client_with_mock_dao
        job_id = uuid4()
        mock_dao.delete.return_value = True

        response = client.delete(f"/jobs/{job_id}")

        assert response.status_code == 200
        assert response.json()["message"] == "Job deleted successfully"
        mock_dao.delete.assert_called_once_with(job_id)

    # These tests do not need the mock DAO, so they use the original 'client' fixture
    def test_create_job_invalid_payload(self, client):
        """Test job creation with invalid payload."""
        response = client.post("/jobs/", json={"invalid_field": "value"})
        assert response.status_code == 422

    def test_get_job_invalid_uuid(self, client):
        """Test job retrieval with invalid UUID."""
        response = client.get("/jobs/invalid-uuid")
        assert response.status_code == 422
