"""Data access object for job operations."""

import logging
from uuid import UUID

from postgrest.exceptions import APIError
from pydantic import ValidationError
from supabase import Client

from ..models.job import JobCreate, JobModel, JobUpdate

logger = logging.getLogger(__name__)


class JobDAO:
    """Data access object for job-related database operations."""

    def __init__(self, supabase: Client):
        self.supabase = supabase
        self.table_name = "jobs"

    def create(self, job_data: JobCreate) -> JobModel:
        """Create a new job record."""
        logger.debug(f"Creating job with data: {job_data}")
        try:
            insert_data = {"content": job_data.content}
            logger.debug(f"Insert data: {insert_data}")

            logger.debug(f"Inserting into table: {self.table_name}")
            result = self.supabase.table(self.table_name).insert(insert_data).execute()
            logger.debug(f"Insert result: {result}")

            if not result.data:
                logger.error("No data returned from insert")
                raise APIError({"message": "Failed to create job"})

            created_job = JobModel(**result.data[0])
            logger.debug(f"Created job model: {created_job}")
            return created_job
        except APIError as e:
            logger.error(f"APIError creating job: {e}")
            raise Exception(f"Database error creating job: {e}") from e
        except Exception as e:
            logger.error(f"Unexpected error creating job: {e}", exc_info=True)
            raise Exception(f"Database error creating job: {e}") from e

    def get_by_id(self, job_id: UUID) -> JobModel | None:
        """Get a job by its ID."""
        try:
            result = self.supabase.table(self.table_name).select("*").eq("id", str(job_id)).execute()

            if not result.data:
                return None

            return JobModel(**result.data[0])
        except APIError as e:
            raise Exception(f"Database error getting job: {e}") from e
        except ValidationError as e:
            raise Exception(f"Database error getting job: {e}") from e

    def get_all(self, limit: int = 100, offset: int = 0) -> list[JobModel]:
        """Get all jobs with pagination."""
        try:
            result = (
                self.supabase.table(self.table_name).select("*").range(offset, offset + limit - 1).execute()
            )

            return [JobModel(**job) for job in result.data]
        except APIError as e:
            raise Exception(f"Database error getting jobs: {e}") from e

    def update(self, job_id: UUID, job_data: JobUpdate) -> JobModel | None:
        """Update an existing job."""
        try:
            update_data = {k: v for k, v in job_data.model_dump(exclude_unset=True).items() if v is not None}

            if not update_data:
                return self.get_by_id(job_id)

            result = self.supabase.table(self.table_name).update(update_data).eq("id", str(job_id)).execute()

            if not result.data:
                return None

            return JobModel(**result.data[0])
        except APIError as e:
            raise Exception(f"Database error updating job: {e}") from e

    def delete(self, job_id: UUID) -> bool:
        """Delete a job by its ID."""
        try:
            result = self.supabase.table(self.table_name).delete().eq("id", str(job_id)).execute()

            return len(result.data) > 0
        except APIError as e:
            raise Exception(f"Database error deleting job: {e}") from e
