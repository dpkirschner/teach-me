"""Tests for the GenericSQLAlchemyDAO."""

import pytest
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from teach_me.dao.alchemy.generic_dao import (
    GenericSQLAlchemyDAO,
)


class FakeORMItem:
    """A fake SQLAlchemy ORM model for testing."""

    def __init__(self, id: int | None = None, name: str | None = None, **kwargs):
        self.id = id
        self.name = name
        # Handle any additional kwargs that might come from model_dump()
        for key, value in kwargs.items():
            setattr(self, key, value)


class FakePydanticItem(BaseModel):
    """A fake Pydantic model for testing."""

    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str


class FakeItemCreate(BaseModel):
    """A fake Pydantic create model."""

    name: str


class FakeItemUpdate(BaseModel):
    """A fake Pydantic update model."""

    name: str | None = None


class FakeItemDAO(GenericSQLAlchemyDAO[FakeORMItem, FakePydanticItem, FakeItemCreate, FakeItemUpdate]):
    """A concrete DAO implementation for testing the generic base class."""

    def _orm_to_pydantic(self, db_obj: FakeORMItem) -> FakePydanticItem:
        return FakePydanticItem.model_validate(db_obj)


@pytest.fixture
def mock_session(mocker):
    """Fixture for a mocked SQLAlchemy Session."""
    return mocker.Mock(spec=Session)


@pytest.fixture
def fake_item_dao(mock_session):
    """Fixture to provide an instance of the concrete DAO."""
    return FakeItemDAO(orm_model=FakeORMItem, session=mock_session)


@pytest.mark.unit
class TestGenericSQLAlchemyDAO:
    """Test cases for the GenericSQLAlchemyDAO."""

    def test_create(self, fake_item_dao, mock_session):
        """Test the create method."""
        create_data = FakeItemCreate(name="New Item")

        # Mock refresh to simulate database setting the ID
        def refresh_side_effect(obj):
            obj.id = 1  # Simulate database-assigned ID

        mock_session.refresh.side_effect = refresh_side_effect

        result = fake_item_dao.create(create_data)

        mock_session.add.assert_called_once()
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once()
        assert result.id == 1
        assert result.name == "New Item"

    def test_get_by_id_found(self, fake_item_dao, mock_session):
        """Test the get_by_id method when an item is found."""
        mock_orm_obj = FakeORMItem(id=1, name="Found Item")
        mock_session.get.return_value = mock_orm_obj

        result = fake_item_dao.get_by_id(1)

        mock_session.get.assert_called_once_with(FakeORMItem, 1)
        assert result is not None
        assert result.id == 1
        assert result.name == "Found Item"

    def test_get_by_id_not_found(self, fake_item_dao, mock_session):
        """Test the get_by_id method when an item is not found."""
        mock_session.get.return_value = None
        result = fake_item_dao.get_by_id(99)
        assert result is None

    def test_update_found(self, fake_item_dao, mock_session):
        """Test the update method when an item is found."""
        update_data = FakeItemUpdate(name="Updated Name")
        mock_orm_obj = FakeORMItem(id=1, name="Original Name")
        mock_session.get.return_value = mock_orm_obj

        result = fake_item_dao.update(1, update_data)

        assert mock_orm_obj.name == "Updated Name"
        mock_session.flush.assert_called_once()
        mock_session.refresh.assert_called_once_with(mock_orm_obj)
        assert result is not None
        assert result.id == 1
        assert result.name == "Updated Name"

    def test_update_not_found(self, fake_item_dao, mock_session):
        """Test the update method when an item is not found."""
        update_data = FakeItemUpdate(name="Updated Name")
        mock_session.get.return_value = None
        result = fake_item_dao.update(99, update_data)
        assert result is None

    def test_delete_found(self, fake_item_dao, mock_session):
        """Test the delete method when an item is found."""
        mock_orm_obj = FakeORMItem(id=1, name="To Delete")
        mock_session.get.return_value = mock_orm_obj

        result = fake_item_dao.delete(1)

        mock_session.delete.assert_called_once_with(mock_orm_obj)
        mock_session.flush.assert_called_once()
        assert result is True

    def test_delete_not_found(self, fake_item_dao, mock_session):
        """Test the delete method when an item is not found."""
        mock_session.get.return_value = None
        result = fake_item_dao.delete(99)
        mock_session.delete.assert_not_called()
        assert result is False
