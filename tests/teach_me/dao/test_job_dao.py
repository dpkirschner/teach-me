"""Tests for JobDAO class."""

from datetime import datetime
from uuid import uuid4

import pytest
from postgrest.exceptions import APIError
from pydantic import ValidationError

from teach_me.dao.job_dao import JobDAO
from teach_me.models.job import JobCreate, JobModel, JobUpdate


@pytest.fixture
def mock_table_query(mocker, mock_supabase_client):
    """Fixture that mocks the table query chain and returns the root table mock."""
    mock_table = mocker.Mock()
    mock_supabase_client.table.return_value = mock_table
    return mock_table


@pytest.mark.unit
class TestJobDAO:
    """Test cases for JobDAO."""

    def test_init(self, mock_supabase_client):
        """Test JobDAO initialization."""
        dao = JobDAO(mock_supabase_client)
        assert dao.supabase == mock_supabase_client
        assert dao.table_name == "jobs"

    def test_create(self, job_dao, mock_table_query, mock_supabase_result, sample_job_create):
        """Test successful job creation."""
        mock_data = {
            "id": str(uuid4()),
            "content": sample_job_create.content,
            "created_at": datetime.now().isoformat(),
        }
        result = mock_supabase_result(data=[mock_data])
        mock_table_query.configure_mock(**{"insert.return_value.execute.return_value": result})

        created_job = job_dao.create(sample_job_create)

        assert isinstance(created_job, JobModel)
        assert created_job.content == sample_job_create.content
        mock_table_query.insert.assert_called_with({"content": sample_job_create.content})

    def test_get_by_id_success(self, job_dao, mock_table_query, mock_supabase_result):
        """Test successful job retrieval by ID."""
        job_id = uuid4()
        mock_data = {"id": str(job_id), "content": "Test content", "created_at": datetime.now().isoformat()}
        result = mock_supabase_result(data=[mock_data])
        mock_table_query.configure_mock(
            **{"select.return_value.eq.return_value.execute.return_value": result}
        )

        found_job = job_dao.get_by_id(job_id)

        assert isinstance(found_job, JobModel)
        assert found_job.id == job_id
        mock_table_query.select.assert_called_with("*")
        mock_table_query.select.return_value.eq.assert_called_with("id", str(job_id))

    def test_get_by_id_not_found(self, job_dao, mock_table_query, mock_supabase_result):
        """Test job retrieval when job not found."""
        result = mock_supabase_result(data=[])
        mock_table_query.configure_mock(
            **{"select.return_value.eq.return_value.execute.return_value": result}
        )

        found_job = job_dao.get_by_id(uuid4())

        assert found_job is None

    def test_get_all(self, job_dao, mock_table_query, mock_supabase_result):
        """Test successful retrieval of all jobs."""
        mock_data = [
            {"id": str(uuid4()), "content": "Job 1", "created_at": datetime.now().isoformat()},
            {"id": str(uuid4()), "content": "Job 2", "created_at": datetime.now().isoformat()},
        ]
        result = mock_supabase_result(data=mock_data)
        mock_table_query.configure_mock(
            **{"select.return_value.range.return_value.execute.return_value": result}
        )

        jobs = job_dao.get_all(limit=10, offset=0)

        assert len(jobs) == 2
        assert all(isinstance(job, JobModel) for job in jobs)
        mock_table_query.select.return_value.range.assert_called_with(0, 9)

    def test_update_success(self, job_dao, mock_table_query, mock_supabase_result, sample_job_update):
        """Test successful job update."""
        job_id = uuid4()
        mock_data = {
            "id": str(job_id),
            "content": sample_job_update.content,
            "created_at": datetime.now().isoformat(),
        }
        result = mock_supabase_result(data=[mock_data])
        mock_table_query.configure_mock(
            **{"update.return_value.eq.return_value.execute.return_value": result}
        )

        updated_job = job_dao.update(job_id, sample_job_update)

        assert isinstance(updated_job, JobModel)
        assert updated_job.content == sample_job_update.content
        mock_table_query.update.assert_called_with({"content": sample_job_update.content})
        mock_table_query.update.return_value.eq.assert_called_with("id", str(job_id))

    def test_update_no_changes(self, mocker, job_dao, mock_table_query):
        """Test job update with no changes does not call the database."""
        job_id = uuid4()
        existing_job = JobModel(id=job_id, content="Test content", created_at=datetime.now())
        mocker.patch.object(job_dao, "get_by_id", return_value=existing_job)

        result = job_dao.update(job_id, JobUpdate())

        assert result == existing_job
        job_dao.get_by_id.assert_called_once_with(job_id)
        mock_table_query.update.assert_not_called()

    def test_delete_success(self, job_dao, mock_table_query, mock_supabase_result):
        """Test successful job deletion."""
        job_id = uuid4()
        result = mock_supabase_result(data=[{"id": str(job_id)}])
        mock_table_query.configure_mock(
            **{"delete.return_value.eq.return_value.execute.return_value": result}
        )

        was_deleted = job_dao.delete(job_id)

        assert was_deleted is True
        mock_table_query.delete.return_value.eq.assert_called_with("id", str(job_id))

    def test_delete_not_found(self, job_dao, mock_table_query, mock_supabase_result):
        """Test job deletion when job not found."""
        result = mock_supabase_result(data=[])
        mock_table_query.configure_mock(
            **{"delete.return_value.eq.return_value.execute.return_value": result}
        )

        was_deleted = job_dao.delete(uuid4())

        assert was_deleted is False

    @pytest.mark.parametrize(
        "method, kwargs, mock_chain, error_message",
        [
            ("create", {"job_data": JobCreate(content="c")}, "insert.execute", "Database error creating job"),
            ("get_by_id", {"job_id": uuid4()}, "select.eq.execute", "Database error getting job"),
            ("get_all", {}, "select.range.execute", "Database error getting jobs"),
            (
                "update",
                {"job_id": uuid4(), "job_data": JobUpdate(content="u")},
                "update.eq.execute",
                "Database error updating job",
            ),
            ("delete", {"job_id": uuid4()}, "delete.eq.execute", "Database error deleting job"),
        ],
    )
    def test_api_errors(self, job_dao, mock_table_query, method, kwargs, mock_chain, error_message):
        """Test that APIErrors are caught and re-raised as generic exceptions."""
        api_error = APIError({"message": "API Error"})
        mock_key = mock_chain.replace(".", ".return_value.") + ".side_effect"
        mock_table_query.configure_mock(**{mock_key: api_error})

        with pytest.raises(Exception, match=error_message):
            getattr(job_dao, method)(**kwargs)

    def test_pydantic_model_validation(self, job_dao, mock_table_query, mock_supabase_result):
        """Test that invalid data from database raises a specific exception."""
        mock_data = [{"id": "invalid-uuid", "created_at": "invalid-date"}]
        result = mock_supabase_result(data=mock_data)
        mock_table_query.configure_mock(
            **{"select.return_value.eq.return_value.execute.return_value": result}
        )

        with pytest.raises(Exception, match="Database error getting job") as exc_info:
            job_dao.get_by_id(uuid4())

        assert isinstance(exc_info.value.__cause__, ValidationError)
