"""Tests for the dependency checker component."""

import importlib.metadata
from unittest.mock import patch

from mermaidmd2pdf.dependencies import DependencyChecker


def test_check_pandoc_installed() -> None:
    """Test Pandoc check when installed."""
    with patch("shutil.which", return_value="/usr/local/bin/pandoc"):
        is_available, error = DependencyChecker.check_pandoc()
        assert is_available
        assert error is None


def test_check_pandoc_not_installed() -> None:
    """Test Pandoc check when not installed."""
    with patch("shutil.which", return_value=None):
        is_available, error = DependencyChecker.check_pandoc()
        assert not is_available
        assert error is not None
        assert "Pandoc is not installed" in error
        assert "brew install pandoc" in error
        assert "apt-get install pandoc" in error
        assert "choco install pandoc" in error


def test_check_python_packages_all_satisfied() -> None:
    """Test Python package check when all packages are satisfied."""
    with patch("importlib.metadata.version") as mock_version:
        mock_version.return_value = "3.5.0"
        is_satisfied, missing = DependencyChecker.check_python_packages()
        assert is_satisfied
        assert missing is None


def test_check_python_packages_wrong_version() -> None:
    """Test Python package check with wrong version."""
    with patch("importlib.metadata.version") as mock_version:
        mock_version.return_value = "3.4.0"
        is_satisfied, missing = DependencyChecker.check_python_packages()
        assert not is_satisfied
        assert missing is not None
        if missing:  # Type guard
            assert len(missing) > 0
            assert "markdown>=3.5.0" in missing[0]


def test_check_python_packages_missing() -> None:
    """Test Python package check with missing package."""
    with patch("importlib.metadata.version") as mock_version:
        mock_version.side_effect = importlib.metadata.PackageNotFoundError()
        is_satisfied, missing = DependencyChecker.check_python_packages()
        assert not is_satisfied
        assert missing is not None
        if missing:  # Type guard
            assert len(missing) > 0
            assert any("markdown" in req for req in missing)


def test_verify_all_success() -> None:
    """Test complete dependency verification when all dependencies are satisfied."""
    with patch("shutil.which", return_value="/usr/local/bin/pandoc"), patch(
        "importlib.metadata.version"
    ) as mock_version:
        mock_version.return_value = "3.5.0"
        is_satisfied, error = DependencyChecker.verify_all()
        assert is_satisfied
        assert error is None


def test_verify_all_missing_pandoc() -> None:
    """Test complete dependency verification with missing Pandoc."""
    with patch("shutil.which", return_value=None):
        is_satisfied, error = DependencyChecker.verify_all()
        assert not is_satisfied
        assert error is not None
        assert "Pandoc is not installed" in error


def test_verify_all_missing_packages() -> None:
    """Test complete dependency verification with missing Python packages."""
    with patch("shutil.which", return_value="/usr/local/bin/pandoc"), patch(
        "importlib.metadata.version"
    ) as mock_version:
        mock_version.side_effect = importlib.metadata.PackageNotFoundError()
        is_satisfied, error = DependencyChecker.verify_all()
        assert not is_satisfied
        assert error is not None
        assert "Missing required Python packages" in error
        assert "uv pip install" in error
