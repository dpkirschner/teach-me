import logging
import sys


def setup_teach_me_logger(level: str = "INFO", format_string: str | None = None) -> logging.Logger:
    """
    Set up and configure the teach_me namespace logger.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_string: Custom format string for log messages

    Returns:
        Configured logger instance
    """
    if format_string is None:
        format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Get or create the teach_me logger
    logger = logging.getLogger("teach_me")

    # Only configure if not already configured
    if not logger.handlers:
        # Set log level
        logger.setLevel(getattr(logging, level.upper()))

        # Create console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(getattr(logging, level.upper()))

        # Create formatter
        formatter = logging.Formatter(format_string)
        console_handler.setFormatter(formatter)

        # Add handler to logger
        logger.addHandler(console_handler)

        # Prevent propagation to root logger
        logger.propagate = False

    return logger


def get_teach_me_logger(name: str) -> logging.Logger:
    """
    Get a child logger under the teach_me namespace.

    Args:
        name: Name for the child logger (e.g., 'api', 'dao', 'models')

    Returns:
        Child logger instance
    """
    return logging.getLogger(f"teach_me.{name}")
