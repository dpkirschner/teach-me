from sqlalchemy.orm import Session

from ..api.models.job import JobRequest, JobUpdateRequest
from ..services.models.job import JobModel
from .alchemy.generic_dao import GenericSQLAlchemyDAO
from .models.job import Job


class JobDAO(GenericSQLAlchemyDAO[Job, JobModel, JobRequest, JobUpdateRequest]):
    """Data access object for Job models."""

    def __init__(self, session: Session):
        super().__init__(orm_model=Job, session=session)

    def _orm_to_pydantic(self, db_obj: Job) -> JobModel:
        """Convert Job ORM model to JobModel Pydantic model."""
        return JobModel.model_validate(db_obj)
