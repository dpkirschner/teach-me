"""Integration tests for database operations."""

import os
from unittest.mock import patch

import pytest

from teach_me.api.models.job import JobRequest, JobUpdateRequest
from teach_me.config.supabase_db import get_supabase_client
from teach_me.dao.job_dao import JobDAO


@pytest.mark.integration
@pytest.mark.skipif(
    not os.getenv("TEST_SUPABASE_URL") or not os.getenv("TEST_SUPABASE_KEY"),
    reason="Integration tests require TEST_SUPABASE_URL and TEST_SUPABASE_KEY",
)
class TestDatabaseIntegration:
    """Integration tests for database operations.

    These tests require a test Supabase instance.
    Set TEST_SUPABASE_URL and TEST_SUPABASE_KEY environment variables.
    """

    @pytest.fixture
    def test_dao(self):
        """Create JobDAO with test database."""
        with patch.dict(
            os.environ,
            {
                "SUPABASE_URL": os.getenv("TEST_SUPABASE_URL"),
                "SUPABASE_KEY": os.getenv("TEST_SUPABASE_KEY"),
            },
        ):
            client = get_supabase_client()
            return JobDAO(client)

    def test_job_crud_operations(self, test_dao):
        """Test complete CRUD cycle with real database."""
        # Create
        job_create = JobRequest(content="Integration test job")
        created_job = test_dao.create(job_create)

        assert created_job.content == "Integration test job"
        assert created_job.id is not None
        job_id = created_job.id

        # Read
        retrieved_job = test_dao.get_by_id(job_id)
        assert retrieved_job is not None
        assert retrieved_job.content == "Integration test job"

        # Update
        job_update = JobUpdateRequest(content="Updated integration test job")
        updated_job = test_dao.update(job_id, job_update)
        assert updated_job is not None
        assert updated_job.content == "Updated integration test job"

        # Delete
        deleted = test_dao.delete(job_id)
        assert deleted is True

        # Verify deletion
        deleted_job = test_dao.get_by_id(job_id)
        assert deleted_job is None

    def test_get_all_pagination(self, test_dao):
        """Test pagination in get_all method."""
        # Create multiple jobs
        created_jobs = []
        for i in range(5):
            job_create = JobRequest(content=f"Test job {i}")
            created_job = test_dao.create(job_create)
            created_jobs.append(created_job)

        try:
            # Test pagination
            page1 = test_dao.get_all(limit=2, offset=0)
            page2 = test_dao.get_all(limit=2, offset=2)

            assert len(page1) <= 2
            assert len(page2) <= 2

            # Verify no overlap
            page1_ids = {job.id for job in page1}
            page2_ids = {job.id for job in page2}
            assert page1_ids.isdisjoint(page2_ids)

        finally:
            # Cleanup
            for job in created_jobs:
                test_dao.delete(job.id)
