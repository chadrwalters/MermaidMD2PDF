"""Dependency checking component for MermaidMD2PDF."""

import importlib.metadata
import shutil
import subprocess
from typing import Dict, List, Optional, Tuple

from packaging.specifiers import SpecifierSet

from mermaidmd2pdf.logging import get_logger

logger = get_logger(__name__)


class DependencyChecker:
    """Checks for required system and Python dependencies."""

    REQUIRED_PACKAGES: Dict[str, str] = {
        "click": ">=8.0.0",
        "pytest": ">=7.0.0",
        "pytest-cov": ">=4.0.0",
    }

    def check_pandoc(self) -> Tuple[bool, Optional[str]]:
        """Check if Pandoc is installed.

        Returns:
            Tuple of (is_available, error_message)
        """
        pandoc_path = shutil.which("pandoc")
        if not pandoc_path:
            return False, "Pandoc is not installed"
        return True, None

    def check_python_packages(self) -> Tuple[bool, List[str]]:
        """Check if required Python packages are installed.

        Returns:
            Tuple of (is_satisfied, missing_packages)
        """
        missing_packages = []
        for package, version_spec in self.REQUIRED_PACKAGES.items():
            try:
                current_version = importlib.metadata.version(package)
                spec_set = SpecifierSet(version_spec)
                if not spec_set.contains(current_version):
                    missing_packages.append(f"{package}{version_spec}")
            except importlib.metadata.PackageNotFoundError:
                missing_packages.append(f"{package}{version_spec}")

        return not bool(missing_packages), missing_packages

    def verify_all(self) -> Tuple[bool, Optional[str]]:
        """Verify all required dependencies.

        Returns:
            Tuple of (satisfied, error_message)
        """
        errors: List[str] = []

        # Check for Pandoc
        logger.debug("Checking for Pandoc...")
        pandoc_ok, pandoc_error = self.check_pandoc()
        if not pandoc_ok:
            errors.append(pandoc_error or "Unknown Pandoc error")

        # Check for Mermaid CLI
        logger.debug("Checking for Mermaid CLI...")
        if not self._check_mermaid_cli():
            errors.append("Mermaid CLI (mmdc) is not installed")

        # Check for XeLaTeX
        logger.debug("Checking for XeLaTeX...")
        if not self._check_xelatex():
            errors.append("XeLaTeX is not installed")

        # Check Python packages
        logger.debug("Checking Python packages...")
        packages_ok, missing_packages = self.check_python_packages()
        if not packages_ok:
            errors.append(f"Missing Python packages: {', '.join(missing_packages)}")

        if errors:
            error_message = "Missing dependencies:\n  • " + "\n  • ".join(errors)
            logger.error(error_message)
            return False, error_message

        logger.debug("All dependencies satisfied")
        return True, None

    def _check_mermaid_cli(self) -> bool:
        """Check if Mermaid CLI is installed.

        Returns:
            True if Mermaid CLI is available, False otherwise
        """
        try:
            subprocess.run(
                ["mmdc", "--version"],
                capture_output=True,
                check=True,
                shell=False,
            )
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _check_xelatex(self) -> bool:
        """Check if XeLaTeX is installed.

        Returns:
            True if XeLaTeX is available, False otherwise
        """
        try:
            subprocess.run(
                ["xelatex", "--version"],
                capture_output=True,
                check=True,
                shell=False,
            )
            return True
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
