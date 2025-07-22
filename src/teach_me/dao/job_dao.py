from sqlalchemy.orm import Session

from ..models.data.job import Job
from ..models.request.job import JobCreate, JobModel, JobUpdate
from .alchemy.generic_dao import GenericSQLAlchemyDAO


class JobDAO(GenericSQLAlchemyDAO[Job, JobModel, JobCreate, JobUpdate]):
    """Data access object for Job models."""

    def __init__(self, session: Session):
        super().__init__(orm_model=Job, session=session)

    def _orm_to_pydantic(self, db_obj: Job) -> JobModel:
        """Convert Job ORM model to JobModel Pydantic model."""
        return JobModel.model_validate(db_obj)
