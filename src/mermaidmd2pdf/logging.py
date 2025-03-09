"""Logging configuration for MermaidMD2PDF."""

import logging
import sys
from typing import Optional


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration.

    Args:
        verbose: Whether to enable debug logging
    """
    # Create logger
    logger = logging.getLogger("mermaidmd2pdf")
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Create console handler with formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Create formatter
    formatter = logging.Formatter("%(message)s")
    console_handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(console_handler)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Get a logger instance.

    Args:
        name: Optional name for the logger (defaults to mermaidmd2pdf)

    Returns:
        Logger instance
    """
    return logging.getLogger(name or "mermaidmd2pdf")
