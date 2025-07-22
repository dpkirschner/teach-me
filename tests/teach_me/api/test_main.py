"""Tests for the FastAPI endpoints."""

from datetime import datetime
from uuid import uuid4

import pytest
from fastapi.testclient import TestClient

from src.teach_me.api.main import app, get_job_dao
from src.teach_me.models.job import JobCreate, JobModel


@pytest.fixture
def test_client():
    """FastAPI test client."""
    return TestClient(app)


@pytest.fixture
def mock_job_dao(mocker):
    """Fixture to create a mock JobDAO."""
    return mocker.Mock()


@pytest.mark.api
class TestJobAPI:
    """Test cases for Job API endpoints."""

    def test_create_job_success(self, test_client, mock_job_dao):
        """Test successful job creation via API."""
        job_id = uuid4()
        created_at = datetime.now()
        job_content = "Test job content"

        mock_job_dao.create.return_value = JobModel(id=job_id, content=job_content, created_at=created_at)
        app.dependency_overrides[get_job_dao] = lambda: mock_job_dao

        response = test_client.post("/jobs/", json={"content": job_content})

        assert response.status_code == 201
        data = response.json()
        assert data["content"] == job_content
        assert data["id"] == str(job_id)
        assert "created_at" in data

        mock_job_dao.create.assert_called_once()
        create_arg = mock_job_dao.create.call_args[0][0]
        assert isinstance(create_arg, JobCreate)
        assert create_arg.content == job_content

        # Clean up the override
        app.dependency_overrides.clear()

    def test_create_job_dao_error(self, test_client, mock_job_dao):
        """Test job creation when DAO raises error."""
        mock_job_dao.create.side_effect = Exception("Database error")
        app.dependency_overrides[get_job_dao] = lambda: mock_job_dao

        response = test_client.post("/jobs/", json={"content": "Test job content"})

        assert response.status_code == 500
        assert "Database error" in response.json()["detail"]
        app.dependency_overrides.clear()

    def test_get_job_success(self, test_client, mock_job_dao):
        """Test successful job retrieval via API."""
        job_id = uuid4()
        mock_job = JobModel(id=job_id, content="Test job content", created_at=datetime.now())
        mock_job_dao.get_by_id.return_value = mock_job
        app.dependency_overrides[get_job_dao] = lambda: mock_job_dao

        response = test_client.get(f"/jobs/{job_id}")

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(job_id)
        mock_job_dao.get_by_id.assert_called_once_with(job_id)
        app.dependency_overrides.clear()

    def test_get_job_not_found(self, test_client, mock_job_dao):
        """Test job retrieval when job not found."""
        job_id = uuid4()
        mock_job_dao.get_by_id.return_value = None
        app.dependency_overrides[get_job_dao] = lambda: mock_job_dao

        response = test_client.get(f"/jobs/{job_id}")

        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]
        app.dependency_overrides.clear()

    def test_get_jobs_success(self, test_client, mock_job_dao):
        """Test successful retrieval of all jobs via API."""
        job1 = JobModel(id=uuid4(), content="Job 1", created_at=datetime.now())
        job2 = JobModel(id=uuid4(), content="Job 2", created_at=datetime.now())
        mock_job_dao.get_all.return_value = [job1, job2]
        app.dependency_overrides[get_job_dao] = lambda: mock_job_dao

        response = test_client.get("/jobs/")

        assert response.status_code == 200
        data = response.json()
        assert len(data) == 2
        assert data[0]["id"] == str(job1.id)
        assert data[1]["id"] == str(job2.id)
        mock_job_dao.get_all.assert_called_once_with(limit=100, offset=0)
        app.dependency_overrides.clear()

    def test_get_jobs_with_pagination(self, test_client, mock_job_dao):
        """Test job retrieval with pagination parameters."""
        mock_job_dao.get_all.return_value = []
        app.dependency_overrides[get_job_dao] = lambda: mock_job_dao

        response = test_client.get("/jobs/?limit=50&offset=10")

        assert response.status_code == 200
        mock_job_dao.get_all.assert_called_once_with(limit=50, offset=10)
        app.dependency_overrides.clear()

    def test_update_job_success(self, test_client, mock_job_dao):
        """Test successful job update via API."""
        job_id = uuid4()
        updated_job = JobModel(id=job_id, content="Updated content", created_at=datetime.now())
        mock_job_dao.update.return_value = updated_job
        app.dependency_overrides[get_job_dao] = lambda: mock_job_dao

        response = test_client.put(f"/jobs/{job_id}", json={"content": "Updated content"})

        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(job_id)
        assert data["content"] == "Updated content"

        mock_job_dao.update.assert_called_once()
        update_args = mock_job_dao.update.call_args[0]
        assert update_args[0] == job_id
        assert update_args[1].content == "Updated content"
        app.dependency_overrides.clear()

    def test_update_job_not_found(self, test_client, mock_job_dao):
        """Test job update when job not found."""
        job_id = uuid4()
        mock_job_dao.update.return_value = None
        app.dependency_overrides[get_job_dao] = lambda: mock_job_dao

        response = test_client.put(f"/jobs/{job_id}", json={"content": "Updated content"})

        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]
        app.dependency_overrides.clear()

    def test_delete_job_success(self, test_client, mock_job_dao):
        """Test successful job deletion via API."""
        job_id = uuid4()
        mock_job_dao.delete.return_value = True
        app.dependency_overrides[get_job_dao] = lambda: mock_job_dao

        response = test_client.delete(f"/jobs/{job_id}")

        assert response.status_code == 200
        assert response.json()["message"] == "Job deleted successfully"
        mock_job_dao.delete.assert_called_once_with(job_id)
        app.dependency_overrides.clear()

    def test_delete_job_not_found(self, test_client, mock_job_dao):
        """Test job deletion when job not found."""
        job_id = uuid4()
        mock_job_dao.delete.return_value = False
        app.dependency_overrides[get_job_dao] = lambda: mock_job_dao

        response = test_client.delete(f"/jobs/{job_id}")

        assert response.status_code == 404
        assert "Job not found" in response.json()["detail"]
        app.dependency_overrides.clear()

    def test_create_job_invalid_payload(self, test_client):
        """Test job creation with invalid payload."""
        response = test_client.post("/jobs/", json={"invalid_field": "value"})
        assert response.status_code == 422

    def test_get_job_invalid_uuid(self, test_client):
        """Test job retrieval with invalid UUID."""
        response = test_client.get("/jobs/invalid-uuid")
        assert response.status_code == 422
