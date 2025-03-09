"""File validation component for MermaidMD2PDF."""

import os
from pathlib import Path
from typing import Optional, Tuple

from mermaidmd2pdf.logging import get_logger

logger = get_logger(__name__)


class FileValidator:
    """Validates input and output files."""

    def validate_input_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate the input Markdown file.

        Args:
            file_path: Path to the input file

        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return False, f"Input file does not exist: {file_path}"
            if not path.is_file():
                return False, f"Input path is not a file: {file_path}"
            if not os.access(path, os.R_OK):
                return False, f"Cannot read input file: {file_path}"
            return True, None
        except Exception as e:
            return False, f"Error validating input file: {e}"

    def validate_output_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate the output PDF file path.

        Args:
            file_path: Path to the output file

        Returns:
            Tuple of (is_valid, error_message)
        """
        error_message = None
        path = Path(file_path)

        # Check if parent directory exists and is writable
        parent = path.parent
        if not parent.exists():
            try:
                parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                error_message = f"Cannot create output directory: {e}"
        elif not os.access(parent, os.W_OK):
            error_message = f"Cannot write to output directory: {parent}"

        # Check if output file is writable
        if path.exists():
            if not path.is_file():
                error_message = f"Output path exists but is not a file: {file_path}"
            elif not os.access(path, os.W_OK):
                error_message = f"Cannot write to existing output file: {file_path}"

        return (True, None) if error_message is None else (False, error_message)
