"""Dependency checking component for MermaidMD2PDF."""

import shutil
import subprocess
from typing import ClassVar, Dict, List, Optional, Tuple

from mermaidmd2pdf.logging import get_logger

logger = get_logger(__name__)


class DependencyChecker:
    """Checks for required system and Python dependencies."""

    REQUIRED_PACKAGES: ClassVar[Dict[str, str]] = {
        "click": ">=8.0.0",
        "pytest": ">=7.0.0",
        "pytest-cov": ">=4.0.0",
    }

    def check_pandoc(self) -> Tuple[bool, Optional[str]]:
        """Check if Pandoc is installed and accessible.

        Returns:
            Tuple of (is_available, error_message)
        """
        pandoc_path = shutil.which("pandoc")
        if not pandoc_path:
            return False, "Pandoc is not installed"

        try:
            result = subprocess.run(
                [pandoc_path, "--version"], capture_output=True, check=False, text=True
            )
            if result.returncode != 0:
                return False, "Pandoc is not accessible"
            return True, None
        except Exception as e:
            return False, f"Error checking Pandoc: {e!s}"

    def check_python_packages(self) -> Tuple[bool, List[str]]:
        """Check if required Python packages are installed.

        Returns:
            Tuple of (is_available, missing_packages)
            where missing_packages is a list of package names that are either
            missing or have version conflicts
        """
        from importlib.metadata import PackageNotFoundError, version

        from packaging.version import parse

        missing: List[str] = []
        for package, version_spec in self.REQUIRED_PACKAGES.items():
            try:
                pkg_version = parse(version(package))
                required_version = parse(version_spec.lstrip(">="))
                if pkg_version < required_version:
                    missing.append(f"{package} (version conflict)")
            except PackageNotFoundError:
                missing.append(package)

        return not bool(missing), missing

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
