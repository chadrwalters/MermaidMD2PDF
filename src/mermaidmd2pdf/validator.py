"""File validation component for MermaidMD2PDF."""

import os
import pathlib
from typing import ClassVar, Optional, Set, Tuple


class FileValidator:
    """Validates input and output files for security and correctness."""

    ALLOWED_INPUT_EXTENSIONS: ClassVar[Set[str]] = {".md", ".markdown"}
    ALLOWED_OUTPUT_EXTENSIONS: ClassVar[Set[str]] = {".pdf"}

    @staticmethod
    def validate_input_file(file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate input file path for security and correctness.

        Args:
            file_path: Path to the input file to validate

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if file is valid, False otherwise
            - error_message: None if valid, error description if invalid
        """
        try:
            path = pathlib.Path(file_path).resolve()

            # Check if file exists
            if not path.exists():
                return False, f"Input file does not exist: {file_path}"

            # Check if path is a file (not a directory)
            if not path.is_file():
                return False, f"Input path is not a file: {file_path}"

            # Check file extension
            if path.suffix.lower() not in FileValidator.ALLOWED_INPUT_EXTENSIONS:
                return False, (
                    f"Invalid input file extension: {path.suffix}. "
                    "Allowed extensions: "
                    f"{', '.join(sorted(FileValidator.ALLOWED_INPUT_EXTENSIONS))}"
                )

            # Check read permissions
            if not os.access(path, os.R_OK):
                return False, f"No read permission for input file: {file_path}"

            # Successful validation
            return True, None

        except (OSError, ValueError) as e:
            return False, f"Error validating input file: {e!s}"

    @staticmethod
    def validate_output_file(file_path: str) -> Tuple[bool, Optional[str]]:
        """Validate output file path for security and correctness.

        Args:
            file_path: Path to the output file to validate

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if file path is valid, False otherwise
            - error_message: None if valid, error description if invalid
        """
        try:
            path = pathlib.Path(file_path).resolve()

            # Check file extension
            if path.suffix.lower() not in FileValidator.ALLOWED_OUTPUT_EXTENSIONS:
                return False, (
                    f"Invalid output file extension: {path.suffix}. "
                    "Allowed extensions: "
                    f"{', '.join(sorted(FileValidator.ALLOWED_OUTPUT_EXTENSIONS))}"
                )

            # Check if parent directory exists and is writable
            parent_dir = path.parent
            if not parent_dir.exists():
                return False, f"Output directory does not exist: {parent_dir}"
            if not os.access(parent_dir, os.W_OK):
                return False, f"No write permission for output directory: {parent_dir}"

            # If file exists, check if it's writable
            if path.exists() and not os.access(path, os.W_OK):
                return (
                    False,
                    f"No write permission for existing output file: {file_path}",
                )

            # Successful validation
            return True, None

        except (OSError, ValueError) as e:
            return False, f"Error validating output file: {e!s}"
