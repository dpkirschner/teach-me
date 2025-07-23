"""Tests for the GenericSQLAlchemyDAO."""

import pytest
from pydantic import BaseModel, ConfigDict
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session, declarative_base

from teach_me.dao.alchemy.generic_dao import (
    GenericSQLAlchemyDAO,
)

Base = declarative_base()


class FakeORMItem(Base):
    """A fake SQLAlchemy ORM model for testing."""

    __tablename__ = "fake_items"

    id = Column(Integer, primary_key=True)
    name = Column(String(50))


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

    def test_create_exception_handling(self, fake_item_dao, mock_session):
        """Test create method exception handling (lines 46-48)."""
        create_data = FakeItemCreate(name="Test")
        mock_session.add.side_effect = Exception("Database error")

        with pytest.raises(Exception, match="Database error"):
            fake_item_dao.create(create_data)

    def test_get_all_with_pagination(self, fake_item_dao, mock_session, mocker):
        """Test get_all method with pagination and logging (lines 65-97)."""
        # Mock the scalar count query
        mock_session.scalar.return_value = 10

        mock_orm_obj1 = FakeORMItem(id=1, name="Item 1")
        mock_orm_obj2 = FakeORMItem(id=2, name="Item 2")

        # Mock the scalars query result
        mock_result = mocker.Mock()
        mock_result.all.return_value = [mock_orm_obj1, mock_orm_obj2]
        mock_session.scalars.return_value = mock_result

        result = fake_item_dao.get_all(limit=5, offset=2)

        # Verify the count query was executed
        mock_session.scalar.assert_called_once()
        # Verify the paginated query was executed
        mock_session.scalars.assert_called_once()
        # Verify results
        assert len(result) == 2
        assert result[0].id == 1
        assert result[1].id == 2

    def test_get_all_empty_table_logging(self, fake_item_dao, mock_session, mocker):
        """Test get_all logs warning for empty table (lines 78-79)."""
        # Mock empty table
        mock_session.scalar.return_value = 0
        mock_result = mocker.Mock()
        mock_result.all.return_value = []
        mock_session.scalars.return_value = mock_result

        # Mock logger
        mock_logger = mocker.patch("teach_me.dao.alchemy.generic_dao.logger")

        result = fake_item_dao.get_all()

        # Verify warning was logged
        mock_logger.warning.assert_any_call("Table 'fake_items' is empty - no FakeORMItem records found")
        assert result == []

    def test_get_all_pagination_warning(self, fake_item_dao, mock_session, mocker):
        """Test get_all logs warning for pagination mismatch (lines 89-93)."""
        # Mock table with records but empty pagination result
        mock_session.scalar.return_value = 100  # Table has records
        mock_result = mocker.Mock()
        mock_result.all.return_value = []  # But pagination returns empty
        mock_session.scalars.return_value = mock_result

        # Mock logger
        mock_logger = mocker.patch("teach_me.dao.alchemy.generic_dao.logger")

        result = fake_item_dao.get_all(offset=200, limit=10)

        # Verify pagination warning was logged
        expected_warning = (
            "Pagination returned 0 FakeORMItem records (offset=200, limit=10) but table has 100 total records"
        )
        mock_logger.warning.assert_any_call(expected_warning)
        assert result == []

    def test_update_exception_handling(self, fake_item_dao, mock_session):
        """Test update method exception handling (lines 121-123)."""
        update_data = FakeItemUpdate(name="Updated")
        mock_orm_obj = FakeORMItem(id=1, name="Original")
        mock_session.get.return_value = mock_orm_obj
        mock_session.flush.side_effect = Exception("Update error")

        with pytest.raises(Exception, match="Update error"):
            fake_item_dao.update(1, update_data)

    def test_delete_exception_handling(self, fake_item_dao, mock_session):
        """Test delete method exception handling (lines 140-142)."""
        mock_orm_obj = FakeORMItem(id=1, name="To Delete")
        mock_session.get.return_value = mock_orm_obj
        mock_session.delete.side_effect = Exception("Delete error")

        with pytest.raises(Exception, match="Delete error"):
            fake_item_dao.delete(1)
