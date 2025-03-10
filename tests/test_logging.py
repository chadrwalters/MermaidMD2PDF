"""Tests for the logging module."""

import logging
from io import StringIO
from unittest.mock import patch

from mermaidmd2pdf.logging import get_logger, setup_logging


def test_setup_logging_default() -> None:
    """Test setup_logging with default settings."""
    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        setup_logging()
        logger = logging.getLogger("mermaidmd2pdf")
        logger.info("Test message")
        assert "Test message" in mock_stdout.getvalue()
        assert logger.level == logging.INFO


def test_setup_logging_verbose() -> None:
    """Test setup_logging with verbose mode."""
    with patch("sys.stdout", new_callable=StringIO) as mock_stdout:
        setup_logging(verbose=True)
        logger = logging.getLogger("mermaidmd2pdf")
        logger.debug("Debug message")
        assert "Debug message" in mock_stdout.getvalue()
        assert logger.level == logging.DEBUG


def test_get_logger_default() -> None:
    """Test get_logger with default name."""
    logger = get_logger()
    assert logger.name == "mermaidmd2pdf"


def test_get_logger_custom_name() -> None:
    """Test get_logger with custom name."""
    logger = get_logger("custom")
    assert logger.name == "custom"
