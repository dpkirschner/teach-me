"""Tests for SQLAlchemy database configuration and session management."""

from unittest.mock import Mock, patch

import pytest
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from teach_me.config.sqlalchemy_db import (
    create_tables,
    get_db_session,
    transactional_session,
)


@pytest.mark.unit
class TestSQLAlchemyDB:
    """Test cases for SQLAlchemy database configuration."""

    @patch("teach_me.config.sqlalchemy_db.Base")
    @patch("teach_me.config.sqlalchemy_db.engine")
    def test_create_tables(self, mock_engine, mock_base):
        """Test create_tables function."""
        mock_metadata = Mock()
        mock_base.metadata = mock_metadata

        create_tables()

        mock_metadata.create_all.assert_called_once_with(bind=mock_engine)

    @patch("teach_me.config.sqlalchemy_db.SessionLocal")
    def test_get_db_session_success(self, mock_session_local):
        """Test get_db_session yields session and closes it."""
        mock_session = Mock(spec=Session)
        mock_session_local.return_value = mock_session

        # Test successful session usage
        session_generator = get_db_session()
        session = next(session_generator)

        assert session is mock_session
        mock_session_local.assert_called_once()

        # Close the generator
        try:
            next(session_generator)
        except StopIteration:
            pass

        mock_session.close.assert_called_once()

    @patch("teach_me.config.sqlalchemy_db.SessionLocal")
    @patch("teach_me.config.sqlalchemy_db.logger")
    def test_get_db_session_exception_handling(self, mock_logger, mock_session_local):
        """Test get_db_session handles exceptions and rolls back."""
        mock_session = Mock(spec=Session)
        mock_session_local.return_value = mock_session

        session_generator = get_db_session()
        next(session_generator)

        # Simulate an exception
        test_exception = SQLAlchemyError("Test error")

        with pytest.raises(SQLAlchemyError):
            session_generator.throw(test_exception)

        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        mock_logger.error.assert_called_once()

    @patch("teach_me.config.sqlalchemy_db.SessionLocal")
    def test_transactional_session_success(self, mock_session_local):
        """Test transactional_session commits on success."""
        mock_session = Mock(spec=Session)
        mock_session_local.return_value = mock_session

        with transactional_session() as session:
            assert session is mock_session
            # Simulate some database operation
            session.execute(text("SELECT 1"))

        mock_session_local.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.rollback.assert_not_called()

    @patch("teach_me.config.sqlalchemy_db.SessionLocal")
    def test_transactional_session_exception_rollback(self, mock_session_local):
        """Test transactional_session rolls back on exception."""
        mock_session = Mock(spec=Session)
        mock_session_local.return_value = mock_session

        test_exception = SQLAlchemyError("Test error")

        with pytest.raises(SQLAlchemyError):
            with transactional_session() as session:
                assert session is mock_session
                raise test_exception

        mock_session_local.assert_called_once()
        mock_session.rollback.assert_called_once()
        mock_session.close.assert_called_once()
        mock_session.commit.assert_not_called()

    def test_database_connection_configuration(self):
        """Test database connection configuration parameters."""
        # Test that the module has the expected configuration
        # We can verify the engine configuration by checking the module attributes
        import teach_me.config.sqlalchemy_db as db_module

        # Verify that engine exists and has expected configuration
        assert hasattr(db_module, "engine")
        assert hasattr(db_module, "SessionLocal")

        # Test that DATABASE_URL is loaded from environment
        assert hasattr(db_module, "DATABASE_URL")
        # Verify it's not the default placeholder value
        assert "[password]" not in db_module.DATABASE_URL

    @patch("teach_me.config.sqlalchemy_db.SessionLocal")
    def test_get_db_session_debug_logging(self, mock_session_local):
        """Test get_db_session debug logging."""
        mock_session = Mock(spec=Session)
        mock_session_local.return_value = mock_session

        with patch("teach_me.config.sqlalchemy_db.logger") as mock_logger:
            session_generator = get_db_session()
            next(session_generator)

            # Close the generator
            try:
                next(session_generator)
            except StopIteration:
                pass

        mock_logger.debug.assert_any_call("Creating new database session")
        mock_logger.debug.assert_any_call("Closing database session")

    @patch("teach_me.config.sqlalchemy_db.SessionLocal")
    def test_transactional_session_multiple_operations(self, mock_session_local):
        """Test transactional_session with multiple operations."""
        mock_session = Mock(spec=Session)
        mock_session_local.return_value = mock_session

        with transactional_session() as session:
            # Simulate multiple database operations
            session.execute(text("INSERT INTO test_table VALUES (1)"))
            session.execute(text("UPDATE test_table SET value = 2"))
            session.flush()

        # Verify session was used and committed
        assert mock_session.execute.call_count == 2
        mock_session.flush.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.close.assert_called_once()
