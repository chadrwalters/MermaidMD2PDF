"""Tests for dependency checking functionality."""

from unittest.mock import patch

from mermaidmd2pdf.dependencies import DependencyChecker


def test_check_python_packages_success() -> None:
    """Test Python packages check success."""
    with patch("importlib.metadata.version", return_value="9.0.0"):
        checker = DependencyChecker()
        is_available, missing = checker.check_python_packages()
        assert is_available
        assert not missing


def test_check_python_packages_failure() -> None:
    """Test Python packages check failure."""
    with patch("importlib.metadata.version", return_value="7.0.0"):
        checker = DependencyChecker()
        is_available, missing = checker.check_python_packages()
        assert not is_available
        assert len(missing) > 0


def test_check_pandoc_installed() -> None:
    """Test Pandoc installation check success."""
    mock_result = type("MockResult", (), {"returncode": 0})()
    with (
        patch("shutil.which", return_value="/usr/local/bin/pandoc"),
        patch("subprocess.run", return_value=mock_result),
    ):
        checker = DependencyChecker()
        is_available, error = checker.check_pandoc()
        assert is_available
        assert error is None


def test_check_pandoc_not_installed() -> None:
    """Test Pandoc installation check failure."""
    with patch("shutil.which", return_value=None):
        checker = DependencyChecker()
        is_available, error = checker.check_pandoc()
        assert not is_available
        assert error == "Pandoc is not installed"


def test_check_mermaid_cli_installed() -> None:
    """Test Mermaid CLI installation check success."""
    mock_result = type("MockResult", (), {"returncode": 0})()
    with patch("subprocess.run", return_value=mock_result):
        checker = DependencyChecker()
        assert checker._check_mermaid_cli()


def test_check_mermaid_cli_not_installed() -> None:
    """Test Mermaid CLI installation check failure."""
    with patch("subprocess.run", side_effect=FileNotFoundError):
        checker = DependencyChecker()
        assert not checker._check_mermaid_cli()


def test_check_xelatex_installed() -> None:
    """Test XeLaTeX installation check success."""
    mock_result = type("MockResult", (), {"returncode": 0})()
    with patch("subprocess.run", return_value=mock_result):
        checker = DependencyChecker()
        assert checker._check_xelatex()


def test_check_xelatex_not_installed() -> None:
    """Test XeLaTeX installation check failure."""
    with patch("subprocess.run", side_effect=FileNotFoundError):
        checker = DependencyChecker()
        assert not checker._check_xelatex()


def test_verify_all_success() -> None:
    """Test verifying all dependencies success."""
    mock_result = type("MockResult", (), {"returncode": 0})()
    with (
        patch("shutil.which", return_value="/usr/local/bin/pandoc"),
        patch("subprocess.run", return_value=mock_result),
        patch("importlib.metadata.version", return_value="9.0.0"),
    ):
        checker = DependencyChecker()
        is_satisfied, error = checker.verify_all()
        assert is_satisfied
        assert error is None


def test_verify_all_failure() -> None:
    """Test verifying all dependencies failure."""
    with (
        patch("shutil.which", return_value=None),
        patch("subprocess.run", side_effect=FileNotFoundError),
        patch("importlib.metadata.version", return_value="7.0.0"),
    ):
        checker = DependencyChecker()
        is_satisfied, error = checker.verify_all()
        assert not is_satisfied
        assert error is not None
        assert "Missing dependencies" in error
