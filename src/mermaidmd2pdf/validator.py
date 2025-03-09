"""File validation component for MermaidMD2PDF."""

import os
from pathlib import Path
from typing import Optional, Tuple

from mermaidmd2pdf.logging import get_logger

logger = get_logger(__name__)


class FileValidator:
    """Validates input and output files."""

    def validate_input_file(self, file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate the input file path.

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
                return False, f"Input file is not readable: {file_path}"
            if path.suffix.lower() != ".md":
                return False, f"Input file {path} is not a Markdown file"

            logger.debug(f"Input file {path} is valid")
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
        try:
            path = Path(file_path)
            parent = path.parent
            error_message = None

            # Check parent directory
            if parent.exists() and not parent.is_dir():
                error_message = f"Parent path is not a directory: {parent}"
            elif not os.access(parent, os.W_OK):
                error_message = f"Parent directory is not writable: {parent}"
            # Check output file
            elif path.exists():
                if not path.is_file():
                    error_message = f"Output path exists but is not a file: {file_path}"
                elif not os.access(path, os.W_OK):
                    error_message = (
                        f"Output file exists but is not writable: {file_path}"
                    )

            return (True, None) if error_message is None else (False, error_message)
        except Exception as e:
            return False, f"Error validating output file: {e}"
