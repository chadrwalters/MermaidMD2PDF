"""Dependency checker component for MermaidMD2PDF."""
import importlib
import shutil
import subprocess
from typing import List, Optional, Tuple

import pkg_resources


class DependencyChecker:
    """Checks system and Python package dependencies."""

    REQUIRED_PACKAGES = {
        "markdown": ">=3.5.0",
        "weasyprint": ">=60.2",
        "click": ">=8.0.0",
    }

    @staticmethod
    def check_pandoc() -> Tuple[bool, Optional[str]]:
        """Check if Pandoc is installed and accessible.

        Returns:
            Tuple of (is_available, error_message)
            - is_available: True if Pandoc is available, False otherwise
            - error_message: None if available, installation instructions if not
        """
        if shutil.which("pandoc") is None:
            return False, (
                "Pandoc is not installed or not in PATH. "
                "Please install Pandoc:\n"
                "- macOS: brew install pandoc\n"
                "- Linux: sudo apt-get install pandoc\n"
                "- Windows: choco install pandoc\n"
                "For more information, visit: https://pandoc.org/installing.html"
            )
        return True, None

    @staticmethod
    def check_python_packages() -> Tuple[bool, Optional[List[str]]]:
        """Check if required Python packages are installed with correct versions.

        Returns:
            Tuple of (all_satisfied, missing_requirements)
            - all_satisfied: True if all requirements are met, False otherwise
            - missing_requirements: List of unmet requirements or None if all satisfied
        """
        missing = []
        for package, version in DependencyChecker.REQUIRED_PACKAGES.items():
            requirement = f"{package}{version}"
            try:
                pkg_resources.require(requirement)
            except (pkg_resources.DistributionNotFound, pkg_resources.VersionConflict):
                missing.append(requirement)

        return not bool(missing), missing if missing else None

    @staticmethod
    def verify_all() -> Tuple[bool, Optional[str]]:
        """Verify all dependencies are satisfied.

        Returns:
            Tuple of (all_satisfied, error_message)
            - all_satisfied: True if all dependencies are satisfied, False otherwise
            - error_message: None if satisfied, detailed error message if not
        """
        # Check Pandoc
        pandoc_ok, pandoc_error = DependencyChecker.check_pandoc()
        if not pandoc_ok:
            return False, pandoc_error

        # Check Python packages
        packages_ok, missing_packages = DependencyChecker.check_python_packages()
        if not packages_ok:
            return False, (
                "Missing required Python packages. Please install:\n"
                f"uv pip install {' '.join(missing_packages)}"
            )

        return True, None
