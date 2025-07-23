"""Tests for the BaseService class."""

from uuid import uuid4

import pytest
from pydantic import BaseModel
from sqlalchemy.orm import Session

from teach_me.dao.alchemy.generic_dao import GenericSQLAlchemyDAO
from teach_me.services.base_service import BaseService


class FakeAPIRequest(BaseModel):
    name: str


class FakeAPIResponse(BaseModel):
    id: int
    name: str


class FakeDAOModel(BaseModel):
    id: int
    name: str


class FakeDAOCreate(BaseModel):
    name: str


class FakeDAOUpdate(BaseModel):
    name: str | None = None


class FakeService(BaseService[FakeAPIRequest, FakeAPIResponse, FakeDAOModel, FakeDAOCreate, FakeDAOUpdate]):
    """A concrete implementation of BaseService for testing."""

    def _api_request_to_dao_create(self, api_request: FakeAPIRequest) -> FakeDAOCreate:
        return FakeDAOCreate(name=api_request.name)

    def _api_request_to_dao_update(self, api_request: FakeAPIRequest) -> FakeDAOUpdate:
        return FakeDAOUpdate(name=api_request.name)

    def _dao_model_to_api_response(self, dao_model: FakeDAOModel) -> FakeAPIResponse:
        return FakeAPIResponse(id=dao_model.id, name=dao_model.name)


@pytest.fixture
def mock_dao(mocker):
    """Fixture for a mocked GenericSQLAlchemyDAO."""
    return mocker.Mock(spec=GenericSQLAlchemyDAO)


@pytest.fixture
def mock_session(mocker):
    """Fixture for a mocked SQLAlchemy Session."""
    return mocker.Mock(spec=Session)


@pytest.fixture
def fake_service(mock_dao, mock_session):
    """Fixture that provides an instance of the concrete FakeService."""
    return FakeService(dao=mock_dao, session=mock_session)


@pytest.mark.unit
class TestBaseService:
    """Test cases for the BaseService class."""

    def test_create_success(self, fake_service, mock_dao, mock_session):
        """Test successful entity creation and transaction commit."""
        api_request = FakeAPIRequest(name="New Item")
        mock_dao.create.return_value = FakeDAOModel(id=1, name="New Item")

        result = fake_service.create(api_request)

        dao_create_arg = mock_dao.create.call_args[0][0]
        assert isinstance(dao_create_arg, FakeDAOCreate)
        assert dao_create_arg.name == "New Item"
        mock_session.commit.assert_called_once()
        assert result.id == 1

    def test_create_failure_rolls_back(self, fake_service, mock_dao, mock_session):
        """Test that a failure during creation rolls back the transaction."""
        mock_dao.create.side_effect = ValueError("DB error")

        with pytest.raises(ValueError, match="DB error"):
            fake_service.create(FakeAPIRequest(name="Bad Item"))

        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()

    def test_get_by_id_found(self, fake_service, mock_dao):
        """Test retrieving an entity by its ID when it exists."""
        entity_id = uuid4()
        mock_dao.get_by_id.return_value = FakeDAOModel(id=1, name="Found Item")

        result = fake_service.get_by_id(entity_id)

        mock_dao.get_by_id.assert_called_once_with(entity_id)
        assert isinstance(result, FakeAPIResponse)
        assert result.id == 1

    def test_get_by_id_not_found(self, fake_service, mock_dao):
        """Test retrieving an entity that does not exist."""
        mock_dao.get_by_id.return_value = None
        result = fake_service.get_by_id(uuid4())
        assert result is None

    def test_update_success(self, fake_service, mock_dao, mock_session):
        """Test successful entity update and transaction commit."""
        entity_id = uuid4()
        api_request = FakeAPIRequest(name="Updated Item")
        mock_dao.update.return_value = FakeDAOModel(id=1, name="Updated Item")

        result = fake_service.update(entity_id, api_request)

        dao_update_arg = mock_dao.update.call_args[0][1]
        assert isinstance(dao_update_arg, FakeDAOUpdate)
        mock_session.commit.assert_called_once()
        assert result.id == 1

    def test_update_not_found(self, fake_service, mock_dao, mock_session):
        """Test updating an entity that does not exist."""
        mock_dao.update.return_value = None
        result = fake_service.update(uuid4(), FakeAPIRequest(name="..."))
        assert result is None
        mock_session.commit.assert_not_called()

    def test_delete_success(self, fake_service, mock_dao, mock_session):
        """Test successful entity deletion and transaction commit."""
        entity_id = uuid4()
        mock_dao.delete.return_value = True

        result = fake_service.delete(entity_id)

        mock_dao.delete.assert_called_once_with(entity_id)
        mock_session.commit.assert_called_once()
        assert result is True

    def test_delete_not_found(self, fake_service, mock_dao, mock_session):
        """Test deleting an entity that does not exist."""
        mock_dao.delete.return_value = False
        result = fake_service.delete(uuid4())
        assert result is False
        mock_session.commit.assert_not_called()

    def test_get_all_success(self, fake_service, mock_dao):
        """Test successful retrieval of all entities."""
        mock_dao.get_all.return_value = [FakeDAOModel(id=1, name="Item 1"), FakeDAOModel(id=2, name="Item 2")]

        result = fake_service.get_all(offset=0, limit=100)

        mock_dao.get_all.assert_called_once_with(offset=0, limit=100)
        assert len(result) == 2
        assert all(isinstance(item, FakeAPIResponse) for item in result)

    def test_get_all_exception_handling(self, fake_service, mock_dao):
        """Test that exceptions in get_all are propagated."""
        mock_dao.get_all.side_effect = Exception("DAO error")

        with pytest.raises(Exception, match="DAO error"):
            fake_service.get_all()

    def test_update_failure_rolls_back(self, fake_service, mock_dao, mock_session):
        """Test that a failure during update rolls back the transaction."""
        entity_id = uuid4()
        mock_dao.update.side_effect = ValueError("Update error")

        with pytest.raises(ValueError, match="Update error"):
            fake_service.update(entity_id, FakeAPIRequest(name="Bad Update"))

        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()

    def test_delete_failure_rolls_back(self, fake_service, mock_dao, mock_session):
        """Test that a failure during delete rolls back the transaction."""
        entity_id = uuid4()
        mock_dao.delete.side_effect = ValueError("Delete error")

        with pytest.raises(ValueError, match="Delete error"):
            fake_service.delete(entity_id)

        mock_session.rollback.assert_called_once()
        mock_session.commit.assert_not_called()
