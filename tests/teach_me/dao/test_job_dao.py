"""Tests for JobDAO class."""

from datetime import datetime
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session

from teach_me.api.models.job import JobRequest, JobUpdateRequest
from teach_me.dao.job_dao import JobDAO
from teach_me.dao.models.job import Job
from teach_me.services.models.job import JobModel


@pytest.fixture
def mock_session(mocker):
    """Fixture for a mocked SQLAlchemy Session."""
    return mocker.Mock(spec=Session)


@pytest.fixture
def job_dao(mock_session):
    """Fixture to provide an instance of JobDAO."""
    return JobDAO(session=mock_session)


@pytest.mark.unit
class TestJobDAO:
    """Test cases for JobDAO."""

    def test_init(self, mock_session):
        """Test JobDAO initialization."""
        dao = JobDAO(mock_session)
        assert dao.session == mock_session
        assert dao.orm_model == Job

    def test_orm_to_pydantic_conversion(self, job_dao):
        """Test the _orm_to_pydantic method."""
        job_id = uuid4()
        created_at = datetime.now()

        # Create a Job ORM object
        job_orm = Job(id=job_id, content="Test content", created_at=created_at)

        # Convert to Pydantic model
        result = job_dao._orm_to_pydantic(job_orm)

        assert isinstance(result, JobModel)
        assert result.id == job_id
        assert result.content == "Test content"
        assert result.created_at == created_at

    def test_create(self, job_dao, mock_session):
        """Test the create method."""
        create_data = JobRequest(content="New job content")

        # Mock refresh to simulate database setting the ID
        def refresh_side_effect(obj):
            obj.id = uuid4()
            obj.created_at = datetime.now()

        mock_session.refresh.side_effect = refresh_side_effect

        result = job_dao.create(create_data)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()
        assert isinstance(result, JobModel)
        assert result.content == "New job content"
        assert result.id is not None
        assert result.created_at is not None

    def test_get_by_id_found(self, job_dao, mock_session):
        """Test the get_by_id method when job is found."""
        job_id = uuid4()
        mock_job = Job(id=job_id, content="Found job", created_at=datetime.now())
        mock_session.get.return_value = mock_job

        result = job_dao.get_by_id(job_id)

        mock_session.get.assert_called_once_with(Job, job_id)
        assert isinstance(result, JobModel)
        assert result.id == job_id
        assert result.content == "Found job"

    def test_get_by_id_not_found(self, job_dao, mock_session):
        """Test the get_by_id method when job is not found."""
        mock_session.get.return_value = None

        result = job_dao.get_by_id(uuid4())

        assert result is None

    def test_update_found(self, job_dao, mock_session):
        """Test the update method when job is found."""
        job_id = uuid4()
        update_data = JobUpdateRequest(content="Updated content")
        mock_job = Job(id=job_id, content="Original content", created_at=datetime.now())
        mock_session.get.return_value = mock_job

        result = job_dao.update(job_id, update_data)

        assert mock_job.content == "Updated content"
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_job)
        assert isinstance(result, JobModel)
        assert result.content == "Updated content"

    def test_update_not_found(self, job_dao, mock_session):
        """Test the update method when job is not found."""
        update_data = JobUpdateRequest(content="Updated content")
        mock_session.get.return_value = None

        result = job_dao.update(uuid4(), update_data)

        assert result is None

    def test_delete_found(self, job_dao, mock_session):
        """Test the delete method when job is found."""
        job_id = uuid4()
        mock_job = Job(id=job_id, content="To delete", created_at=datetime.now())
        mock_session.get.return_value = mock_job

        result = job_dao.delete(job_id)

        mock_session.delete.assert_called_once_with(mock_job)
        mock_session.flush.assert_called_once()
        assert result is True

    def test_delete_not_found(self, job_dao, mock_session):
        """Test the delete method when job is not found."""
        mock_session.get.return_value = None

        result = job_dao.delete(uuid4())

        mock_session.delete.assert_not_called()
        assert result is False
