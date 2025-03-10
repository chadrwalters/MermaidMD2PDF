"""Tests for the utility functions."""

from pathlib import Path
from unittest.mock import patch

import pytest

from mermaidmd2pdf.utils import atomic_write, temp_directory, working_directory


def test_temp_directory_basic() -> None:
    """Test basic temp_directory functionality."""
    with temp_directory() as tmp_dir:
        assert tmp_dir.exists()
        assert tmp_dir.is_dir()
        test_file = tmp_dir / "test.txt"
        test_file.write_text("test")
        assert test_file.exists()
    assert not tmp_dir.exists()


def test_temp_directory_with_base_dir(tmp_path: Path) -> None:
    """Test temp_directory with base directory."""
    base_dir = tmp_path / "base"
    with temp_directory(base_dir=base_dir) as tmp_dir:
        assert tmp_dir.exists()
        assert base_dir in tmp_dir.parents
    assert not tmp_dir.exists()
    assert base_dir.exists()


def test_temp_directory_no_cleanup() -> None:
    """Test temp_directory without cleanup."""
    tmp_dir = None
    with temp_directory(cleanup=False) as td:
        tmp_dir = td
        assert tmp_dir.exists()
    assert tmp_dir.exists()
    # Clean up after test
    tmp_dir.rmdir()


def test_temp_directory_cleanup_error() -> None:
    """Test temp_directory with cleanup error."""
    with patch("shutil.rmtree", side_effect=OSError("Test error")):
        with temp_directory() as tmp_dir:
            assert tmp_dir.exists()
        # Directory should still exist due to cleanup error
        assert tmp_dir.exists()
        # Clean up after test
        tmp_dir.rmdir()


def test_atomic_write_success(tmp_path: Path) -> None:
    """Test successful atomic write."""
    target_file = tmp_path / "output.txt"
    content = "Hello, World!"
    with atomic_write(target_file) as temp_file:
        temp_file.write_text(content)
    assert target_file.exists()
    assert target_file.read_text() == content


def test_atomic_write_failure(tmp_path: Path) -> None:
    """Test atomic write with failure."""
    target_file = tmp_path / "output.txt"
    with pytest.raises(RuntimeError):
        with atomic_write(target_file) as temp_file:
            temp_file.write_text("test")
            raise RuntimeError("Test error")
    assert not target_file.exists()


def test_working_directory() -> None:
    """Test working directory context manager."""
    original_cwd = Path.cwd()
    test_dir = Path("/tmp")
    with working_directory(test_dir) as wd:
        current_dir = Path.cwd()
        assert current_dir.resolve() == test_dir.resolve()
        assert wd.resolve() == test_dir.resolve()
    assert Path.cwd() == original_cwd


def test_working_directory_error() -> None:
    """Test working directory with error."""
    original_cwd = Path.cwd()
    with pytest.raises(RuntimeError):
        with working_directory(Path("/tmp")):
            raise RuntimeError("Test error")
    assert Path.cwd() == original_cwd
