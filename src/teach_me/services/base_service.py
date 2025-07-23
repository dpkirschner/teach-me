"""
Base service class providing CRUD operations with automatic model transformations.
"""

from abc import ABC, abstractmethod
from typing import Generic, TypeVar
from uuid import UUID

from pydantic import BaseModel
from sqlalchemy.orm import Session

from teach_me.dao.alchemy.generic_dao import GenericSQLAlchemyDAO
from teach_me.utils.logging import get_teach_me_logger

# Type variables for service layer
APIRequestType = TypeVar("APIRequestType", bound=BaseModel)
APIResponseType = TypeVar("APIResponseType", bound=BaseModel)
DAOModelType = TypeVar("DAOModelType", bound=BaseModel)
DAOCreateType = TypeVar("DAOCreateType", bound=BaseModel)
DAOUpdateType = TypeVar("DAOUpdateType", bound=BaseModel)


class BaseService(Generic[APIRequestType, APIResponseType, DAOModelType, DAOCreateType, DAOUpdateType], ABC):
    """
    Abstract base service class that provides CRUD operations with automatic model transformations.

    This service layer sits between the API and DAO layers, handling:
    - Model transformations between API schemas and DAO models
    - Business logic encapsulation
    - Transaction coordination
    """

    def __init__(self, dao: GenericSQLAlchemyDAO, session: Session):
        """
        Initialize the service with a DAO instance and database session.

        Args:
            dao: The DAO instance for data access operations
            session: SQLAlchemy database session
        """
        self.dao = dao
        self.session = session
        self.logger = get_teach_me_logger(f"{__name__}.{self.__class__.__name__}")

    @abstractmethod
    def _api_request_to_dao_create(self, api_request: APIRequestType) -> DAOCreateType:
        """
        Convert API request model to DAO create model.

        Args:
            api_request: The API request model

        Returns:
            DAO create model
        """
        pass

    @abstractmethod
    def _api_request_to_dao_update(self, api_request: APIRequestType) -> DAOUpdateType:
        """
        Convert API request model to DAO update model.

        Args:
            api_request: The API request model

        Returns:
            DAO update model
        """
        pass

    @abstractmethod
    def _dao_model_to_api_response(self, dao_model: DAOModelType) -> APIResponseType:
        """
        Convert DAO model to API response model.

        Args:
            dao_model: The DAO model

        Returns:
            API response model
        """
        pass

    def create(self, api_request: APIRequestType) -> APIResponseType:
        """
        Create a new entity.

        Args:
            api_request: The API request model containing creation data

        Returns:
            API response model with the created entity
        """
        self.logger.info(f"Creating new entity with request: {api_request}")

        try:
            # Transform API request to DAO create model
            dao_create = self._api_request_to_dao_create(api_request)

            # Create entity via DAO
            dao_model = self.dao.create(dao_create)

            # Commit the transaction
            self.session.commit()

            # Transform DAO model to API response
            api_response = self._dao_model_to_api_response(dao_model)

            self.logger.info(f"Successfully created entity with ID: {getattr(dao_model, 'id', 'unknown')}")
            return api_response

        except Exception as e:
            self.logger.error(f"Failed to create entity: {str(e)}")
            self.session.rollback()
            raise

    def get_by_id(self, entity_id: UUID) -> APIResponseType | None:
        """
        Retrieve an entity by its ID.

        Args:
            entity_id: The UUID of the entity

        Returns:
            API response model if found, None otherwise
        """
        self.logger.debug(f"Retrieving entity with ID: {entity_id}")

        dao_model = self.dao.get_by_id(entity_id)
        if dao_model is None:
            self.logger.debug(f"Entity with ID {entity_id} not found")
            return None

        api_response = self._dao_model_to_api_response(dao_model)
        self.logger.debug(f"Successfully retrieved entity with ID: {entity_id}")
        return api_response

    def get_all(self, offset: int = 0, limit: int = 100) -> list[APIResponseType]:
        """
        Retrieve all entities with pagination.

        Args:
            offset: Number of entities to skip
            limit: Maximum number of entities to return

        Returns:
            List of API response models
        """
        self.logger.debug(f"Retrieving entities with offset={offset}, limit={limit}")

        dao_models = self.dao.get_all(offset=offset, limit=limit)
        api_responses = [self._dao_model_to_api_response(dao_model) for dao_model in dao_models]

        self.logger.debug(f"Successfully retrieved {len(api_responses)} entities")
        return api_responses

    def update(self, entity_id: UUID, api_request: APIRequestType) -> APIResponseType | None:
        """
        Update an existing entity.

        Args:
            entity_id: The UUID of the entity to update
            api_request: The API request model containing update data

        Returns:
            API response model with the updated entity if found, None otherwise
        """
        self.logger.info(f"Updating entity with ID: {entity_id}")

        try:
            # Transform API request to DAO update model
            dao_update = self._api_request_to_dao_update(api_request)

            # Update entity via DAO
            dao_model = self.dao.update(entity_id, dao_update)
            if dao_model is None:
                self.logger.warning(f"Entity with ID {entity_id} not found for update")
                return None

            # Commit the transaction
            self.session.commit()

            # Transform DAO model to API response
            api_response = self._dao_model_to_api_response(dao_model)

            self.logger.info(f"Successfully updated entity with ID: {entity_id}")
            return api_response

        except Exception as e:
            self.logger.error(f"Failed to update entity with ID {entity_id}: {str(e)}")
            self.session.rollback()
            raise

    def delete(self, entity_id: UUID) -> bool:
        """
        Delete an entity by its ID.

        Args:
            entity_id: The UUID of the entity to delete

        Returns:
            True if the entity was deleted, False if not found
        """
        self.logger.info(f"Deleting entity with ID: {entity_id}")

        try:
            success = self.dao.delete(entity_id)
            if success:
                # Commit the transaction
                self.session.commit()
                self.logger.info(f"Successfully deleted entity with ID: {entity_id}")
            else:
                self.logger.warning(f"Entity with ID {entity_id} not found for deletion")

            return success

        except Exception as e:
            self.logger.error(f"Failed to delete entity with ID {entity_id}: {str(e)}")
            self.session.rollback()
            raise
