"""Utility classes and functions for MermaidMD2PDF."""

import contextlib
import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator, Optional

from mermaidmd2pdf.logging import get_logger

logger = get_logger(__name__)


@contextlib.contextmanager
def temp_directory(
    prefix: str = "mermaidmd2pdf-",
    base_dir: Optional[Path] = None,
    cleanup: bool = True,
) -> Generator[Path, None, None]:
    """Create and manage a temporary directory.

    This context manager creates a temporary directory and ensures proper cleanup
    when the context is exited, even if an exception occurs.

    Args:
        prefix: Prefix for the temporary directory name
        base_dir: Optional base directory for the temporary directory
        cleanup: Whether to clean up the directory on exit

    Yields:
        Path to the temporary directory

    Example:
        >>> with temp_directory() as tmp_dir:
        ...     # Use temporary directory
        ...     (tmp_dir / "file.txt").write_text("Hello")
        >>> # Directory is automatically cleaned up
    """
    temp_dir = None
    try:
        if base_dir:
            base_dir.mkdir(parents=True, exist_ok=True)
            temp_dir = Path(tempfile.mkdtemp(prefix=prefix, dir=str(base_dir)))
        else:
            temp_dir = Path(tempfile.mkdtemp(prefix=prefix))
        logger.debug(f"Created temporary directory: {temp_dir}")
        yield temp_dir
    finally:
        if cleanup and temp_dir and temp_dir.exists():
            try:
                shutil.rmtree(temp_dir)
                logger.debug(f"Cleaned up temporary directory: {temp_dir}")
            except Exception as e:
                logger.warning(
                    f"Failed to clean up temporary directory {temp_dir}: {e}"
                )


@contextlib.contextmanager
def atomic_write(
    filepath: Path, mode: str = "w", encoding: Optional[str] = None
) -> Generator[Path, None, None]:
    """Write to a file atomically using a temporary file.

    This context manager ensures that file writes are atomic by writing to a
    temporary file first and then moving it to the target location. This prevents
    partial writes and maintains file consistency.

    Args:
        filepath: Path to the target file
        mode: File open mode ('w' or 'wb')
        encoding: Optional file encoding (for text mode)

    Yields:
        Path to the temporary file to write to

    Example:
        >>> with atomic_write(Path("output.txt")) as tmp_path:
        ...     tmp_path.write_text("Hello World")
        >>> # File is atomically moved to output.txt
    """
    temp_file = None
    try:
        # Create temporary file in the same directory
        temp_file = Path(
            tempfile.mktemp(
                prefix=f".{filepath.name}.", suffix=".tmp", dir=str(filepath.parent)
            )
        )
        yield temp_file
        # Atomic move to target location
        temp_file.replace(filepath)
        logger.debug(f"Atomically wrote file: {filepath}")
    finally:
        # Clean up temporary file if something went wrong
        if temp_file and temp_file.exists():
            try:
                temp_file.unlink()
            except Exception as e:
                logger.warning(f"Failed to clean up temporary file {temp_file}: {e}")


@contextlib.contextmanager
def working_directory(path: Path) -> Generator[Path, None, None]:
    """Temporarily change working directory.

    This context manager changes the current working directory and ensures
    it is restored when the context is exited, even if an exception occurs.

    Args:
        path: Path to temporarily change to

    Yields:
        The new working directory path

    Example:
        >>> with working_directory(Path("/tmp")) as wd:
        ...     # Current directory is /tmp
        ...     print(os.getcwd())
        >>> # Original directory is restored
    """
    prev_cwd = Path.cwd()
    try:
        os.chdir(str(path))
        logger.debug(f"Changed working directory to: {path}")
        yield path
    finally:
        os.chdir(str(prev_cwd))
        logger.debug(f"Restored working directory to: {prev_cwd}")
