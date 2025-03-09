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
            file_path: Path to the output PDF file

        Returns:
            Tuple of (is_valid, error_message)
        """
        error_msg = None
        try:
            # Check if parent directory exists and is writable
            parent_dir = os.path.dirname(file_path)
            if parent_dir and not os.path.exists(parent_dir):
                try:
                    os.makedirs(parent_dir)
                except OSError as e:
                    error_msg = f"Failed to create output directory: {e}"

            # Check if output file is writable
            if not error_msg:
                if os.path.exists(file_path):
                    if not os.access(file_path, os.W_OK):
                        error_msg = f"Output file {file_path} is not writable"
                # Check if parent directory is writable
                elif not os.access(os.path.dirname(file_path), os.W_OK):
                    error_msg = f"Parent directory of {file_path} is not writable"

        except Exception as e:
            error_msg = f"Error validating output file: {e}"

        return (True, None) if not error_msg else (False, error_msg)
