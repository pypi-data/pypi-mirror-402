"""Tests for logging module."""

import logging
from unittest import mock

import pytest

from scalene_mcp.logging import configure_logging, get_logger


class TestGetLogger:
    """Test get_logger function."""

    def test_get_logger_basic(self):
        """Test getting a logger."""
        logger = get_logger("test")
        assert isinstance(logger, logging.Logger)
        assert "scalene_mcp" in logger.name

    def test_get_logger_with_prefix(self):
        """Test logger name gets scalene_mcp prefix if missing."""
        logger = get_logger("mymodule")
        assert logger.name == "scalene_mcp.mymodule"

    def test_get_logger_already_prefixed(self):
        """Test logger name not double-prefixed if already has prefix."""
        logger = get_logger("scalene_mcp.already_prefixed")
        assert logger.name == "scalene_mcp.already_prefixed"


class TestConfigureLogging:
    """Test configure_logging function."""

    def test_configure_logging_enabled(self):
        """Test logging configuration when enabled."""
        with mock.patch("fastmcp.settings.log_enabled", True):
            # Should not raise
            configure_logging(level="INFO")

    def test_configure_logging_disabled(self):
        """Test logging configuration when disabled."""
        with mock.patch("fastmcp.settings.log_enabled", False):
            # Should return early and not configure
            configure_logging(level="INFO")
            # No assertion needed - just verify it doesn't crash

    def test_configure_logging_with_level(self):
        """Test configuring logging with specific level."""
        with mock.patch("fastmcp.settings.log_enabled", True):
            configure_logging(level="DEBUG")

    def test_configure_logging_with_kwargs(self):
        """Test configuring logging with rich handler kwargs."""
        with mock.patch("fastmcp.settings.log_enabled", True):
            configure_logging(level="INFO", show_time=True, show_level=True)
