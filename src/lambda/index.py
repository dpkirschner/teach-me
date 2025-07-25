"""
Sample Lambda function handler.
"""

import json
import logging
import os

# Configure logging using environment variable
LOG_LEVEL = os.environ.get("LOG_LEVEL", "INFO")
logging.basicConfig(level=getattr(logging, LOG_LEVEL))
logger = logging.getLogger(__name__)


def handler(event: dict, context: dict) -> dict:
    """
    Lambda function handler.

    Args:
        event: The event dict that contains the data sent to the Lambda function
        context: The context in which the function is called

    Returns:
        dict: Response with statusCode and body
    """
    logger.info(f"Received event: {json.dumps(event)}")

    return {
        "statusCode": 200,
        "body": json.dumps({"message": "Hello from Lambda!", "event": event, "log_level": LOG_LEVEL}),
    }
