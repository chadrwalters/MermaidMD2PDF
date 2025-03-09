"""Tests for the dependency checker component."""

import importlib.metadata
from unittest.mock import patch

from mermaidmd2pdf.dependencies import DependencyChecker


def test_check_pandoc_installed() -> None:
    """Test Pandoc check when installed."""
    with patch("shutil.which", return_value="/usr/local/bin/pandoc"):
        checker = DependencyChecker()
        is_available, error = checker.check_pandoc()
        assert is_available
        assert error is None


def test_check_pandoc_not_installed() -> None:
    """Test Pandoc check when not installed."""
    with patch("shutil.which", return_value=None):
        checker = DependencyChecker()
        is_available, error = checker.check_pandoc()
        assert not is_available
        assert "Pandoc is not installed" in str(error)


def test_check_python_packages_all_satisfied() -> None:
    """Test Python package check when all packages are satisfied."""
    with patch("importlib.metadata.version") as mock_version:
        mock_version.return_value = (
            "60.2"  # This version satisfies all package requirements
        )
        checker = DependencyChecker()
        is_satisfied, missing = checker.check_python_packages()
        assert is_satisfied
        assert not missing


def test_check_python_packages_wrong_version() -> None:
    """Test Python package check with wrong version."""
    with patch("importlib.metadata.version") as mock_version:
        mock_version.return_value = "3.4.0"
        checker = DependencyChecker()
        is_satisfied, missing = checker.check_python_packages()
        assert not is_satisfied
        assert missing


def test_check_python_packages_missing() -> None:
    """Test Python package check with missing package."""
    with patch("importlib.metadata.version") as mock_version:
        mock_version.side_effect = importlib.metadata.PackageNotFoundError()
        checker = DependencyChecker()
        is_satisfied, missing = checker.check_python_packages()
        assert not is_satisfied
        assert missing


def test_verify_all_success() -> None:
    """Test complete dependency verification when all dependencies are satisfied."""
    with patch("shutil.which", return_value="/usr/local/bin/pandoc"), patch(
        "importlib.metadata.version"
    ) as mock_version:
        mock_version.return_value = (
            "60.2"  # This version satisfies all package requirements
        )
        checker = DependencyChecker()
        is_satisfied, error = checker.verify_all()
        assert is_satisfied
        assert error is None


def test_verify_all_missing_pandoc() -> None:
    """Test complete dependency verification with missing Pandoc."""
    with patch("shutil.which", return_value=None):
        checker = DependencyChecker()
        is_satisfied, error = checker.verify_all()
        assert not is_satisfied
        assert "Pandoc is not installed" in str(error)


def test_verify_all_missing_packages() -> None:
    """Test complete dependency verification with missing Python packages."""
    with patch("shutil.which", return_value="/usr/local/bin/pandoc"), patch(
        "importlib.metadata.version"
    ) as mock_version:
        mock_version.side_effect = importlib.metadata.PackageNotFoundError()
        checker = DependencyChecker()
        is_satisfied, error = checker.verify_all()
        assert not is_satisfied
        assert "Missing Python packages" in str(error)
