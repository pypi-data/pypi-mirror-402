"""
Logging configuration for LeenO MCP Server.
"""

import logging
import sys
from typing import Optional

from ..config import get_config


def setup_logging(level: Optional[str] = None) -> None:
    """
    Configure logging for the server.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR). If None, uses config.
    """
    config = get_config()

    if level is None:
        level = config.log_level

    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Configure root logger
    logging.basicConfig(
        level=numeric_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        stream=sys.stderr
    )

    # Set up file handler if configured
    if config.log_file:
        file_handler = logging.FileHandler(config.log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        logging.getLogger().addHandler(file_handler)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the given name.

    Args:
        name: Logger name (usually __name__)

    Returns:
        Configured logger
    """
    return logging.getLogger(name)
