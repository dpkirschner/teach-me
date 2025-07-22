from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from ...utils.logging import get_teach_me_logger

# Define Type Variables for the generic DAO
ORMModelType = TypeVar("ORMModelType")
PydanticModelType = TypeVar("PydanticModelType", bound=BaseModel)
PydanticCreateType = TypeVar("PydanticCreateType", bound=BaseModel)
PydanticUpdateType = TypeVar("PydanticUpdateType", bound=BaseModel)

logger = get_teach_me_logger("dao.generic")


class GenericSQLAlchemyDAO(
    Generic[ORMModelType, PydanticModelType, PydanticCreateType, PydanticUpdateType], ABC
):
    """A generic Data Access Object for SQLAlchemy models."""

    def __init__(self, orm_model: type[ORMModelType], session: Session):
        self.orm_model = orm_model
        self.session = session

    @abstractmethod
    def _orm_to_pydantic(self, db_obj: ORMModelType) -> PydanticModelType:
        """Convert ORM model to Pydantic model. Must be implemented by subclasses."""
        pass

    def create(self, model_data: PydanticCreateType) -> PydanticModelType:
        """Create a new record."""
        model_name = self.orm_model.__name__
        logger.debug(f"Creating new {model_name} record")

        try:
            db_obj = self.orm_model(**model_data.model_dump())
            self.session.add(db_obj)
            self.session.flush()
            self.session.refresh(db_obj)

            logger.info(f"Successfully created {model_name} record with ID: {getattr(db_obj, 'id', 'N/A')}")
            return self._orm_to_pydantic(db_obj)
        except Exception as e:
            logger.error(f"Failed to create {model_name} record: {e}")
            raise

    def get_by_id(self, obj_id: Any) -> PydanticModelType | None:
        """Get a record by its ID."""
        model_name = self.orm_model.__name__
        logger.debug(f"Fetching {model_name} record by ID: {obj_id}")

        db_obj = self.session.get(self.orm_model, obj_id)
        if db_obj:
            logger.debug(f"Found {model_name} record with ID: {obj_id}")
            return self._orm_to_pydantic(db_obj)
        else:
            logger.warning(f"{model_name} record not found with ID: {obj_id}")
            return None

    def get_all(self, limit: int = 100, offset: int = 0) -> list[PydanticModelType]:
        """Get all records with pagination."""
        table_name = getattr(self.orm_model, "__tablename__", "unknown")
        model_name = self.orm_model.__name__

        logger.debug(f"Fetching {model_name} records with pagination: limit={limit}, offset={offset}")

        # Get total count for operational monitoring
        logger.debug(f"About to execute count query for {table_name}")
        count_stmt = select(func.count()).select_from(self.orm_model)
        logger.debug(f"Count statement prepared, executing...")
        total_count = self.session.scalar(count_stmt) or 0
        logger.debug(f"Count query completed, result: {total_count}")

        # Log table metrics for monitoring and debugging
        if total_count == 0:
            logger.warning(f"Table '{table_name}' is empty - no {model_name} records found")
        else:
            logger.debug(f"Table '{table_name}' contains {total_count} {model_name} records")

        # Execute paginated query
        stmt = select(self.orm_model).offset(offset).limit(limit)
        db_objs = self.session.scalars(stmt).all()

        # Log pagination results
        returned_count = len(db_objs)
        if returned_count == 0 and total_count > 0:
            logger.warning(
                f"Pagination returned 0 {model_name} records "
                f"(offset={offset}, limit={limit}) but table has {total_count} total records"
            )
        else:
            logger.debug(f"Successfully retrieved {returned_count} {model_name} records from offset {offset}")

        return [self._orm_to_pydantic(obj) for obj in db_objs]

    def update(self, obj_id: Any, model_data: PydanticUpdateType) -> PydanticModelType | None:
        """Update an existing record."""
        model_name = self.orm_model.__name__
        logger.debug(f"Updating {model_name} record with ID: {obj_id}")

        db_obj = self.session.get(self.orm_model, obj_id)
        if not db_obj:
            logger.warning(f"Cannot update - {model_name} record not found with ID: {obj_id}")
            return None

        try:
            update_data = model_data.model_dump(exclude_unset=True)
            updated_fields = list(update_data.keys())

            for field, value in update_data.items():
                setattr(db_obj, field, value)

            self.session.flush()
            self.session.refresh(db_obj)

            logger.info(f"Successfully updated {model_name} record {obj_id}, fields: {updated_fields}")
            return self._orm_to_pydantic(db_obj)
        except Exception as e:
            logger.error(f"Failed to update {model_name} record {obj_id}: {e}")
            raise

    def delete(self, obj_id: Any) -> bool:
        """Delete a record by its ID."""
        model_name = self.orm_model.__name__
        logger.debug(f"Deleting {model_name} record with ID: {obj_id}")

        db_obj = self.session.get(self.orm_model, obj_id)
        if not db_obj:
            logger.warning(f"Cannot delete - {model_name} record not found with ID: {obj_id}")
            return False

        try:
            self.session.delete(db_obj)
            self.session.flush()
            logger.info(f"Successfully deleted {model_name} record with ID: {obj_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to delete {model_name} record {obj_id}: {e}")
            raise
