"""Tests for the dependency checker component."""
import os
from unittest.mock import patch

import pytest

from mermaidmd2pdf.dependencies import DependencyChecker


def test_check_pandoc_installed():
    """Test Pandoc detection when installed."""
    with patch("shutil.which", return_value="/usr/local/bin/pandoc"):
        is_available, error = DependencyChecker.check_pandoc()
        assert is_available
        assert error is None


def test_check_pandoc_not_installed():
    """Test Pandoc detection when not installed."""
    with patch("shutil.which", return_value=None):
        is_available, error = DependencyChecker.check_pandoc()
        assert not is_available
        assert "Pandoc is not installed" in error
        assert "brew install pandoc" in error
        assert "apt-get install pandoc" in error
        assert "choco install pandoc" in error


def test_check_python_packages_all_satisfied():
    """Test Python package verification when all requirements are met."""
    with patch("importlib.metadata.version", return_value="3.5.0"):
        is_satisfied, missing = DependencyChecker.check_python_packages()
        assert is_satisfied
        assert missing is None


def test_check_python_packages_missing():
    """Test Python package verification when requirements are missing."""

    def mock_version(package):
        if package == "markdown":
            raise importlib.metadata.PackageNotFoundError()
        return "1.0.0"

    with patch("importlib.metadata.version", side_effect=mock_version):
        is_satisfied, missing = DependencyChecker.check_python_packages()
        assert not is_satisfied
        assert len(missing) == 1
        assert "markdown>=3.5.0" in missing


def test_check_python_packages_version_mismatch():
    """Test Python package verification when version requirements are not met."""

    def mock_version(package):
        if package == "markdown":
            return "3.4.0"  # Lower than required 3.5.0
        return "60.2.0"  # Matches requirement for other packages

    with patch("importlib.metadata.version", side_effect=mock_version):
        is_satisfied, missing = DependencyChecker.check_python_packages()
        assert not is_satisfied
        assert len(missing) == 1
        assert "markdown>=3.5.0" in missing


def test_verify_all_success():
    """Test complete dependency verification when all requirements are met."""
    with patch("shutil.which", return_value="/usr/local/bin/pandoc"), patch(
        "importlib.metadata.version", return_value="3.5.0"
    ):
        is_satisfied, error = DependencyChecker.verify_all()
        assert is_satisfied
        assert error is None


def test_verify_all_missing_pandoc():
    """Test complete dependency verification when Pandoc is missing."""
    with patch("shutil.which", return_value=None), patch(
        "importlib.metadata.version", return_value="3.5.0"
    ):
        is_satisfied, error = DependencyChecker.verify_all()
        assert not is_satisfied
        assert "Pandoc is not installed" in error


def test_verify_all_missing_packages():
    """Test complete dependency verification when Python packages are missing."""

    def mock_version(package):
        if package == "markdown":
            raise importlib.metadata.PackageNotFoundError()
        return "60.2.0"

    with patch("shutil.which", return_value="/usr/local/bin/pandoc"), patch(
        "importlib.metadata.version", side_effect=mock_version
    ):
        is_satisfied, error = DependencyChecker.verify_all()
        assert not is_satisfied
        assert "Missing required Python packages" in error
        assert "markdown>=3.5.0" in error
