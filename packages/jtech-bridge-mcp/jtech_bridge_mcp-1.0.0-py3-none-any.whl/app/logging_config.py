"""
Logging Configuration Module

Provides structured logging setup with configurable levels and formats.
Follows the Single Responsibility Principle - handles only logging concerns.
"""

import logging
import sys

from app.config import get_settings


class LoggerFactory:
    """
    Factory for creating configured loggers.

    Implements the Factory Pattern for consistent logger creation
    across the application with centralized configuration.
    """

    _initialized: bool = False
    _root_logger: logging.Logger | None = None

    @classmethod
    def setup(cls) -> None:
        """
        Initialize the root logger with application settings.

        This method is idempotent - calling it multiple times
        will not create duplicate handlers.
        """
        if cls._initialized:
            return

        settings = get_settings()

        # Configure root logger
        root = logging.getLogger("mcp_bridge")
        root.setLevel(getattr(logging, settings.log_level))

        # Remove existing handlers to prevent duplicates
        root.handlers.clear()

        # Create console handler with formatting
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setLevel(getattr(logging, settings.log_level))

        # Create formatter
        formatter = logging.Formatter(settings.log_format)
        console_handler.setFormatter(formatter)

        # Add handler to root logger
        root.addHandler(console_handler)

        cls._root_logger = root
        cls._initialized = True

    @classmethod
    def get_logger(cls, name: str) -> logging.Logger:
        """
        Get a logger instance with the given name.

        Args:
            name: The name for the logger (typically __name__).

        Returns:
            logging.Logger: A configured logger instance.
        """
        cls.setup()

        # Create child logger under our root
        full_name = f"mcp_bridge.{name}" if not name.startswith("mcp_bridge") else name
        return logging.getLogger(full_name)


def get_logger(name: str) -> logging.Logger:
    """
    Convenience function to get a configured logger.

    Args:
        name: The name for the logger (typically __name__).

    Returns:
        logging.Logger: A configured logger instance.

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")
    """
    return LoggerFactory.get_logger(name)
