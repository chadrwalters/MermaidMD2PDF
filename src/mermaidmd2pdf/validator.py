"""File validation component for MermaidMD2PDF."""

import os
from pathlib import Path
from typing import Optional, Tuple

from mermaidmd2pdf.logging import get_logger

logger = get_logger(__name__)


class FileValidator:
    """Validates input and output files."""

    def __init__(self) -> None:
        """Initialize the validator."""
        self.VALID_INPUT_EXTENSIONS = {".md", ".markdown"}
        self.VALID_OUTPUT_EXTENSIONS = {".pdf"}

    def validate_input_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate an input file.

        Args:
            file_path: Path to the input file

        Returns:
            Tuple of (is_valid, error_message)
        """
        path = Path(file_path)

        if not path.exists():
            return False, f"File does not exist: {file_path}"

        if not path.is_file():
            return False, f"Path is not a file: {file_path}"

        if path.suffix.lower() not in self.VALID_INPUT_EXTENSIONS:
            return (
                False,
                f"File is not a Markdown file (extension: {path.suffix}). "
                f"Expected: {', '.join(self.VALID_INPUT_EXTENSIONS)}",
            )

        if not os.access(path, os.R_OK):
            return False, f"File is not readable: {file_path}"

        return True, None

    def validate_output_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate an output file.

        Args:
            file_path: Path to the output file

        Returns:
            Tuple of (is_valid, error_message)
        """
        path = Path(file_path)
        if path.suffix.lower() not in self.VALID_OUTPUT_EXTENSIONS:
            return (
                False,
                f"File must have .pdf extension, got: {path.suffix}",
            )

        # Create parent directory if it doesn't exist
        path.parent.mkdir(parents=True, exist_ok=True)

        # Check if we can write to the output directory
        if not os.access(path.parent, os.W_OK):
            return False, f"Directory is not writable: {path.parent}"

        # If file exists, check if we can overwrite it
        if path.exists() and not os.access(path, os.W_OK):
            return False, f"File exists and is not writable: {file_path}"

        return True, None
