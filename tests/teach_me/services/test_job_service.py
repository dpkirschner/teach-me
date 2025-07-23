"""Tests for the JobService class."""

from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from teach_me.api.models.job import JobRequest, JobResponse, JobUpdateRequest
from teach_me.dao.job_dao import JobDAO
from teach_me.services.job_service import JobService
from teach_me.services.models.job import JobModel


@pytest.fixture
def mock_job_dao(mocker):
    """Fixture for a mocked JobDAO."""
    return mocker.Mock(spec=JobDAO)


@pytest.fixture
def mock_session(mocker):
    """Fixture for a mocked SQLAlchemy Session."""
    return mocker.Mock(spec=Session)


@pytest.fixture
def job_service(mock_job_dao, mock_session):
    """Fixture that provides an instance of JobService."""
    return JobService(job_dao=mock_job_dao, session=mock_session)


@pytest.fixture
def sample_job_model():
    """Sample JobModel for testing."""
    return JobModel(id=uuid4(), content="Test job content", created_at=datetime.now())


@pytest.mark.unit
class TestJobService:
    """Test cases for the JobService class."""

    def test_api_request_to_dao_create(self, job_service):
        """Test _api_request_to_dao_create returns the same object."""
        request = JobRequest(content="Test content")
        result = job_service._api_request_to_dao_create(request)
        assert result is request

    def test_api_request_to_dao_update(self, job_service):
        """Test _api_request_to_dao_update converts to JobUpdateRequest."""
        request = JobRequest(content="Updated content")
        result = job_service._api_request_to_dao_update(request)
        assert isinstance(result, JobUpdateRequest)
        assert result.content == "Updated content"

    def test_dao_model_to_api_response(self, job_service, sample_job_model):
        """Test _dao_model_to_api_response converts to JobResponse."""
        result = job_service._dao_model_to_api_response(sample_job_model)
        assert isinstance(result, JobResponse)
        assert result.id == sample_job_model.id
        assert result.content == sample_job_model.content
        assert result.created_at == sample_job_model.created_at

    def test_create_job_success(self, job_service, mock_job_dao, mock_session, sample_job_model):
        """Test successful job creation with validation."""
        request = JobRequest(content="Valid content")
        mock_job_dao.create.return_value = sample_job_model

        result = job_service.create_job(request)

        assert isinstance(result, JobResponse)
        mock_job_dao.create.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_create_job_empty_content_after_strip(self, job_service):
        """Test create_job raises error for empty content after stripping."""
        request = JobRequest(content="   \n\t   ")

        with pytest.raises(ValueError, match="Job content cannot be empty or only whitespace"):
            job_service.create_job(request)

    def test_create_job_content_too_long(self, job_service):
        """Test create_job raises error for content exceeding limit."""
        request = JobRequest(content="x" * 10001)

        with pytest.raises(ValueError, match="Job content cannot exceed 10,000 characters"):
            job_service.create_job(request)

    def test_update_job_success(self, job_service, mock_job_dao, mock_session, sample_job_model):
        """Test successful job update with validation."""
        job_id = uuid4()
        request = JobRequest(content="Valid updated content")
        mock_job_dao.update.return_value = sample_job_model

        result = job_service.update_job(job_id, request)

        assert isinstance(result, JobResponse)
        mock_job_dao.update.assert_called_once()
        mock_session.commit.assert_called_once()

    def test_update_job_empty_content_after_strip(self, job_service):
        """Test update_job raises error for empty content after stripping."""
        job_id = uuid4()
        request = JobRequest(content="   \n\t   ")

        with pytest.raises(ValueError, match="Job content cannot be empty or only whitespace"):
            job_service.update_job(job_id, request)

    def test_update_job_content_too_long(self, job_service):
        """Test update_job raises error for content exceeding limit."""
        job_id = uuid4()
        request = JobRequest(content="x" * 10001)

        with pytest.raises(ValueError, match="Job content cannot exceed 10,000 characters"):
            job_service.update_job(job_id, request)

    def test_get_job_by_id_delegates_to_base(self, job_service, mocker):
        """Test get_job_by_id delegates to base class method."""
        job_id = uuid4()
        mock_response = JobResponse(id=job_id, content="Test", created_at=datetime.now())

        # Mock the base class method
        mocker.patch.object(job_service, "get_by_id", return_value=mock_response)

        result = job_service.get_job_by_id(job_id)

        job_service.get_by_id.assert_called_once_with(job_id)
        assert result == mock_response

    def test_get_all_jobs_enforces_limit(self, job_service, mocker):
        """Test get_all_jobs enforces maximum limit and logs warning."""
        mock_jobs = [JobResponse(id=uuid4(), content="Test", created_at=datetime.now())]

        # Mock the base class method and logger
        mocker.patch.object(job_service, "get_all", return_value=mock_jobs)
        mock_logger = mocker.patch.object(job_service, "logger")

        result = job_service.get_all_jobs(offset=0, limit=1500)

        job_service.get_all.assert_called_once_with(offset=0, limit=1000)
        mock_logger.warning.assert_called_once_with("Requested limit exceeded maximum, capped at 1000")
        assert result == mock_jobs

    def test_get_all_jobs_normal_limit(self, job_service, mocker):
        """Test get_all_jobs with normal limit doesn't trigger warning."""
        mock_jobs = [JobResponse(id=uuid4(), content="Test", created_at=datetime.now())]

        # Mock the base class method and logger
        mocker.patch.object(job_service, "get_all", return_value=mock_jobs)
        mock_logger = mocker.patch.object(job_service, "logger")

        result = job_service.get_all_jobs(offset=10, limit=50)

        job_service.get_all.assert_called_once_with(offset=10, limit=50)
        mock_logger.warning.assert_not_called()
        assert result == mock_jobs

    def test_delete_job_delegates_to_base(self, job_service, mocker):
        """Test delete_job delegates to base class method."""
        job_id = uuid4()

        # Mock the base class method
        mocker.patch.object(job_service, "delete", return_value=True)

        result = job_service.delete_job(job_id)

        job_service.delete.assert_called_once_with(job_id)
        assert result is True
