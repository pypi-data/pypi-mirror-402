"""Logging configuration for the Scalene MCP server."""

import logging
from typing import Any, Literal

from rich.logging import RichHandler

import fastmcp.settings


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance, namespaced under 'scalene_mcp'.

    Args:
        name: The name for the logger.

    Returns:
        A configured logger instance.
    """
    if not name.startswith("scalene_mcp."):
        name = f"scalene_mcp.{name}"
    return logging.getLogger(name)


def configure_logging(
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] | int = "INFO",
    **rich_kwargs: Any,
) -> None:
    """
    Configure logging for the entire application using RichHandler.

    Args:
        level: The minimum log level to display.
        **rich_kwargs: Additional arguments for RichHandler.
    """
    if not fastmcp.settings.log_enabled:
        return

    # Set up the root logger for 'scalene_mcp'
    root_logger = logging.getLogger("scalene_mcp")
    root_logger.setLevel(level)

    # Create a RichHandler for pretty, colorful console output
    handler = RichHandler(
        rich_tracebacks=fastmcp.settings.enable_rich_tracebacks, **rich_kwargs
    )

    # Add the handler to the root logger
    if not root_logger.handlers:
        root_logger.addHandler(handler)

    # Propagate logs to the root to ensure they are handled
    root_logger.propagate = True


# Initialize logging with default settings
configure_logging()
