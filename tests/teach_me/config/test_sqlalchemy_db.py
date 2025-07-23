"""Tests for SQLAlchemy database configuration and session management."""

from unittest.mock import Mock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from teach_me.config.sqlalchemy_db import Database, db


@pytest.mark.unit
class TestSQLAlchemyDB:
    """Test cases for SQLAlchemy database configuration."""

    @patch("teach_me.config.sqlalchemy_db.Base")
    def test_create_tables(self, mock_base):
        """Test create_tables method."""
        mock_metadata = Mock()
        mock_base.metadata = mock_metadata

        db.create_tables()

        mock_metadata.create_all.assert_called_once_with(bind=db.engine)

    def test_get_db_session_success(self):
        """Test get_db_session yields session and closes it."""
        with patch.object(db, "SessionLocal") as mock_session_local:
            mock_session = Mock(spec=Session)
            mock_session_local.return_value = mock_session

            # Test successful session usage
            session_generator = db.get_db_session()
            session = next(session_generator)

            assert session is mock_session
            mock_session_local.assert_called_once()

            # Close the generator
            try:
                next(session_generator)
            except StopIteration:
                pass

            mock_session.close.assert_called_once()

    @patch("teach_me.config.sqlalchemy_db.logger")
    def test_get_db_session_exception_handling(self, mock_logger):
        """Test get_db_session handles exceptions and rolls back."""
        with patch.object(db, "SessionLocal") as mock_session_local:
            mock_session = Mock(spec=Session)
            mock_session_local.return_value = mock_session

            session_generator = db.get_db_session()
            next(session_generator)

            # Simulate an exception
            test_exception = SQLAlchemyError("Test error")

            with pytest.raises(SQLAlchemyError):
                session_generator.throw(test_exception)

            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()
            mock_logger.error.assert_called_once()

    def test_transactional_session_success(self):
        """Test transactional_session commits on success."""
        with patch.object(db, "SessionLocal") as mock_session_local:
            mock_session = Mock(spec=Session)
            mock_session_local.return_value = mock_session

            with db.transactional_session() as session:
                assert session is mock_session
                # Simulate some database operation
                session.execute(text("SELECT 1"))

            mock_session_local.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()
            mock_session.rollback.assert_not_called()

    def test_transactional_session_exception_rollback(self):
        """Test transactional_session rolls back on exception."""
        with patch.object(db, "SessionLocal") as mock_session_local:
            mock_session = Mock(spec=Session)
            mock_session_local.return_value = mock_session

            test_exception = SQLAlchemyError("Test error")

            with pytest.raises(SQLAlchemyError):
                with db.transactional_session() as session:
                    assert session is mock_session
                    raise test_exception

            mock_session_local.assert_called_once()
            mock_session.rollback.assert_called_once()
            mock_session.close.assert_called_once()
            mock_session.commit.assert_not_called()

    def test_database_connection_configuration(self):
        """Test database connection configuration parameters."""
        # Test that the global db instance has the expected configuration
        assert hasattr(db, "engine")
        assert hasattr(db, "SessionLocal")

        # Verify db is a Database instance
        assert isinstance(db, Database)

    def test_get_db_session_context_manager(self):
        """Test get_db_session works as context manager."""
        with patch.object(db, "SessionLocal") as mock_session_local:
            mock_session = Mock(spec=Session)
            mock_session_local.return_value = mock_session

            session_generator = db.get_db_session()
            session = next(session_generator)

            assert session is mock_session
            mock_session_local.assert_called_once()

    def test_transactional_session_multiple_operations(self):
        """Test transactional_session with multiple operations."""
        with patch.object(db, "SessionLocal") as mock_session_local:
            mock_session = Mock(spec=Session)
            mock_session_local.return_value = mock_session

            with db.transactional_session() as session:
                # Simulate multiple database operations
                session.execute(text("INSERT INTO test_table VALUES (1)"))
                session.execute(text("UPDATE test_table SET value = 2"))
                session.flush()

            # Verify session was used and committed
            assert mock_session.execute.call_count == 2
            mock_session.flush.assert_called_once()
            mock_session.commit.assert_called_once()
            mock_session.close.assert_called_once()
