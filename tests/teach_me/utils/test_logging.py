"""Tests for the logging utilities."""

import logging
from unittest.mock import patch

import pytest

from teach_me.utils.logging import get_teach_me_logger, setup_teach_me_logger


@pytest.fixture(autouse=True)
def clean_logger():
    """Fixture to ensure the teach_me logger is clean for each test."""
    logger = logging.getLogger("teach_me")
    logger.handlers.clear()
    logger.propagate = True
    yield
    logger.handlers.clear()


@pytest.mark.unit
class TestLoggingUtils:
    """Test cases for logging utility functions."""

    def test_setup_teach_me_logger_default_config(self):
        """Test setup_teach_me_logger with default configuration."""
        logger = setup_teach_me_logger()

        assert logger.name == "teach_me"
        assert logger.level == logging.INFO
        assert len(logger.handlers) == 1
        assert isinstance(logger.handlers[0], logging.StreamHandler)
        assert logger.propagate is False

    def test_setup_teach_me_logger_custom_level(self):
        """Test setup_teach_me_logger with custom log level."""
        logger = setup_teach_me_logger(level="DEBUG")

        assert logger.level == logging.DEBUG
        assert logger.handlers[0].level == logging.DEBUG

    def test_setup_teach_me_logger_custom_format(self):
        """Test setup_teach_me_logger with custom format string."""
        custom_format = "%(name)s - %(message)s"
        logger = setup_teach_me_logger(format_string=custom_format)

        formatter = logger.handlers[0].formatter
        assert formatter._fmt == custom_format

    def test_setup_teach_me_logger_idempotent(self):
        """Test that setup_teach_me_logger doesn't add duplicate handlers."""
        logger1 = setup_teach_me_logger()
        initial_handler_count = len(logger1.handlers)

        logger2 = setup_teach_me_logger()

        assert logger1 is logger2
        assert len(logger2.handlers) == initial_handler_count

    def test_get_teach_me_logger(self):
        """Test get_teach_me_logger creates child loggers correctly."""
        logger = get_teach_me_logger("test_module")

        assert logger.name == "teach_me.test_module"
        assert logger.parent.name == "teach_me"

    def test_get_teach_me_logger_different_names(self):
        """Test get_teach_me_logger with different module names."""
        api_logger = get_teach_me_logger("api")
        dao_logger = get_teach_me_logger("dao")

        assert api_logger.name == "teach_me.api"
        assert dao_logger.name == "teach_me.dao"
        assert api_logger is not dao_logger

    @patch("teach_me.utils.logging.logging.getLogger")
    def test_logger_configuration_calls(self, mock_get_logger):
        """Test that logging configuration makes expected calls."""
        mock_logger = mock_get_logger.return_value
        mock_logger.handlers = []

        setup_teach_me_logger(level="WARNING")

        mock_get_logger.assert_called_with("teach_me")
        mock_logger.setLevel.assert_called_with(logging.WARNING)
        mock_logger.addHandler.assert_called_once()

    def test_invalid_log_level_raises_error(self):
        """Test that invalid log level raises AttributeError."""
        with pytest.raises(AttributeError):
            setup_teach_me_logger(level="INVALID_LEVEL")
