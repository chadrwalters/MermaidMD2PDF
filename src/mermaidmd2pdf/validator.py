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
            path = Path(file_path).resolve()
            if not path.exists():
                return False, f"Input file {path} does not exist"
            if not path.is_file():
                return False, f"Input path {path} is not a file"
            if not os.access(path, os.R_OK):
                return False, f"Input file {path} is not readable"
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
            path = Path(file_path).resolve()
            parent = path.parent

            # Check if parent directory exists and is writable
            if parent.exists():
                if not os.access(parent, os.W_OK):
                    return False, f"Output directory {parent} is not writable"
            else:
                try:
                    parent.mkdir(parents=True)
                except (OSError, PermissionError) as e:
                    return False, f"Cannot create output directory {parent}: {e}"

            # Check if output file exists and is writable
            if path.exists():
                if not os.access(path, os.W_OK):
                    return False, f"Output file {path} exists but is not writable"
            else:
                # Try to create a temporary file to verify write access
                try:
                    path.touch()
                    path.unlink()
                except (OSError, PermissionError) as e:
                    return False, f"Cannot write to output file {path}: {e}"

            if path.suffix.lower() != ".pdf":
                return False, f"Output file {path} must have .pdf extension"

            logger.debug(f"Output file {path} is valid")
            return True, None

        except Exception as e:
            return False, f"Error validating output file: {e}"
