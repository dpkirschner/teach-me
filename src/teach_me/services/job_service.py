"""
Job service implementation providing business logic and model transformations.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from teach_me.dao.job_dao import JobDAO
from teach_me.models.request.job import JobCreate, JobModel, JobUpdate
from teach_me.schemas.job import JobRequest, JobResponse
from teach_me.services.base_service import BaseService
from teach_me.utils.logging import get_teach_me_logger


class JobService(BaseService[JobRequest, JobResponse, JobModel, JobCreate, JobUpdate]):
    """
    Job service that handles business logic and model transformations for Job entities.

    This service provides:
    - Automatic conversion between API schemas (JobRequest/JobResponse) and DAO models
    - Business logic encapsulation for job operations
    - Transaction management for job-related operations
    """

    def __init__(self, job_dao: JobDAO, session: Session):
        """
        Initialize the job service.

        Args:
            job_dao: The job DAO instance
            session: SQLAlchemy database session
        """
        super().__init__(job_dao, session)
        self.job_dao = job_dao
        self.logger = get_teach_me_logger(__name__)

    def _api_request_to_dao_create(self, api_request: JobRequest) -> JobCreate:
        """
        Convert JobRequest to JobCreate model.

        Args:
            api_request: The JobRequest from the API

        Returns:
            JobCreate model for DAO operations
        """
        return JobCreate(content=api_request.content)

    def _api_request_to_dao_update(self, api_request: JobRequest) -> JobUpdate:
        """
        Convert JobRequest to JobUpdate model.

        Args:
            api_request: The JobRequest from the API

        Returns:
            JobUpdate model for DAO operations
        """
        return JobUpdate(content=api_request.content)

    def _dao_model_to_api_response(self, dao_model: JobModel) -> JobResponse:
        """
        Convert JobModel to JobResponse.

        Args:
            dao_model: The JobModel from the DAO

        Returns:
            JobResponse for API responses
        """
        return JobResponse(id=dao_model.id, content=dao_model.content, created_at=dao_model.created_at)

    def create_job(self, job_request: JobRequest) -> JobResponse:
        """
        Create a new job with business logic validation.

        Args:
            job_request: The job creation request

        Returns:
            The created job response
        """
        self.logger.info(f"Creating new job with content length: {len(job_request.content)}")

        # Business logic: validate content is not empty after stripping whitespace
        if not job_request.content.strip():
            raise ValueError("Job content cannot be empty or only whitespace")

        # Business logic: limit content length (example business rule)
        if len(job_request.content) > 10000:
            raise ValueError("Job content cannot exceed 10,000 characters")

        return self.create(job_request)

    def update_job(self, job_id: UUID, job_request: JobRequest) -> JobResponse | None:
        """
        Update an existing job with business logic validation.

        Args:
            job_id: The ID of the job to update
            job_request: The job update request

        Returns:
            The updated job response if found, None otherwise
        """
        self.logger.info(f"Updating job {job_id} with content length: {len(job_request.content)}")

        # Business logic: validate content is not empty after stripping whitespace
        if not job_request.content.strip():
            raise ValueError("Job content cannot be empty or only whitespace")

        # Business logic: limit content length (example business rule)
        if len(job_request.content) > 10000:
            raise ValueError("Job content cannot exceed 10,000 characters")

        return self.update(job_id, job_request)

    def get_job_by_id(self, job_id: UUID) -> JobResponse | None:
        """
        Retrieve a job by its ID.

        Args:
            job_id: The UUID of the job

        Returns:
            The job response if found, None otherwise
        """
        return self.get_by_id(job_id)

    def get_all_jobs(self, offset: int = 0, limit: int = 100) -> list[JobResponse]:
        """
        Retrieve all jobs with pagination.

        Args:
            offset: Number of jobs to skip
            limit: Maximum number of jobs to return

        Returns:
            List of job responses
        """
        # Business logic: enforce maximum limit
        if limit > 1000:
            limit = 1000
            self.logger.warning(f"Requested limit exceeded maximum, capped at {limit}")

        return self.get_all(offset=offset, limit=limit)

    def delete_job(self, job_id: UUID) -> bool:
        """
        Delete a job by its ID.

        Args:
            job_id: The UUID of the job to delete

        Returns:
            True if the job was deleted, False if not found
        """
        return self.delete(job_id)
