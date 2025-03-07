"""Tests for the file validator component."""

import os
import pathlib
import tempfile
from typing import Generator

import pytest
from mermaidmd2pdf.validator import FileValidator


@pytest.fixture
def temp_dir() -> Generator[pathlib.Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield pathlib.Path(temp_dir)


def test_validate_input_file_valid_markdown(temp_dir: pathlib.Path) -> None:
    """Test validation of a valid markdown input file."""
    test_file = temp_dir / "test.md"
    test_file.write_text("# Test")

    is_valid, error = FileValidator.validate_input_file(str(test_file))
    assert is_valid
    assert error is None


def test_validate_input_file_nonexistent() -> None:
    """Test validation of a nonexistent input file."""
    is_valid, error = FileValidator.validate_input_file("nonexistent.md")
    assert not is_valid
    assert "does not exist" in str(error)


def test_validate_input_file_wrong_extension(temp_dir: pathlib.Path) -> None:
    """Test validation of a file with wrong extension."""
    test_file = temp_dir / "test.txt"
    test_file.write_text("test")

    is_valid, error = FileValidator.validate_input_file(str(test_file))
    assert not is_valid
    assert "Invalid input file extension" in str(error)


def test_validate_input_file_directory(temp_dir: pathlib.Path) -> None:
    """Test validation when input is a directory."""
    is_valid, error = FileValidator.validate_input_file(str(temp_dir))
    assert not is_valid
    assert "not a file" in str(error)


def test_validate_input_file_no_read_permission(temp_dir: pathlib.Path) -> None:
    """Test validation of a file without read permission."""
    test_file = temp_dir / "test.md"
    test_file.write_text("# Test")
    os.chmod(test_file, 0o000)  # Remove all permissions

    is_valid, error = FileValidator.validate_input_file(str(test_file))
    assert not is_valid
    assert "No read permission" in str(error)

    os.chmod(test_file, 0o644)  # Restore permissions for cleanup


def test_validate_output_file_valid_pdf(temp_dir: pathlib.Path) -> None:
    """Test validation of a valid PDF output path."""
    test_file = temp_dir / "test.pdf"

    is_valid, error = FileValidator.validate_output_file(str(test_file))
    assert is_valid
    assert error is None


def test_validate_output_file_wrong_extension(temp_dir: pathlib.Path) -> None:
    """Test validation of output file with wrong extension."""
    test_file = temp_dir / "test.txt"

    is_valid, error = FileValidator.validate_output_file(str(test_file))
    assert not is_valid
    assert "Invalid output file extension" in str(error)


def test_validate_output_file_nonexistent_directory() -> None:
    """Test validation of output file in nonexistent directory."""
    is_valid, error = FileValidator.validate_output_file("nonexistent/test.pdf")
    assert not is_valid
    assert "directory does not exist" in str(error)


def test_validate_output_file_no_write_permission(temp_dir: pathlib.Path) -> None:
    """Test validation of output file in non-writable directory."""
    os.chmod(temp_dir, 0o500)  # Read and execute only

    test_file = temp_dir / "test.pdf"
    is_valid, error = FileValidator.validate_output_file(str(test_file))
    assert not is_valid
    assert "No write permission" in str(error)

    os.chmod(temp_dir, 0o755)  # Restore permissions for cleanup
