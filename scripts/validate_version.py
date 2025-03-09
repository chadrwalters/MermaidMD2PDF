#!/usr/bin/env python3
"""Script to validate version consistency across files."""

import json
import re
import sys
from pathlib import Path
from typing import Callable, Dict, List, Optional, Tuple

from packaging.version import parse


class VersionValidator:
    """Validates version consistency across project files."""

    def __init__(self) -> None:
        """Initialize the version validator."""
        self.project_root = Path(__file__).parent.parent
        self.version_files: Dict[str, Callable[[], Optional[str]]] = {
            "pyproject.toml": self._get_pyproject_version,
            "package.json": self._get_package_json_version,
            "src/mermaidmd2pdf/__init__.py": self._get_init_version,
        }

    def _get_pyproject_version(self) -> Optional[str]:
        """Get version from pyproject.toml.

        Returns:
            Version string or None if not found
        """
        pyproject_path = self.project_root / "pyproject.toml"
        if not pyproject_path.exists():
            return None

        content = pyproject_path.read_text()
        match = re.search(r'^version = "([^"]+)"', content, re.MULTILINE)
        return match.group(1) if match else None

    def _get_package_json_version(self) -> Optional[str]:
        """Get version from package.json.

        Returns:
            Version string or None if not found
        """
        package_json_path = self.project_root / "package.json"
        if not package_json_path.exists():
            return None

        try:
            data = json.loads(package_json_path.read_text())
            version = data.get("version")
            return str(version) if version is not None else None
        except json.JSONDecodeError:
            return None

    def _get_init_version(self) -> Optional[str]:
        """Get version from __init__.py.

        Returns:
            Version string or None if not found
        """
        init_path = self.project_root / "src" / "mermaidmd2pdf" / "__init__.py"
        if not init_path.exists():
            return None

        content = init_path.read_text()
        match = re.search(r'^__version__ = "([^"]+)"', content, re.MULTILINE)
        return match.group(1) if match else None

    def validate_versions(self) -> Tuple[bool, List[str]]:
        """Validate version consistency across all files.

        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors: List[str] = []
        versions: Dict[str, str] = {}

        # Get versions from all files
        for file_name, getter in self.version_files.items():
            version = getter()
            if version is None:
                errors.append(f"Could not find version in {file_name}")
            else:
                versions[file_name] = version

        # Check if all versions are valid semantic versions
        for file_name, version in versions.items():
            try:
                parse(version)
            except ValueError:
                errors.append(f"Invalid semantic version in {file_name}: {version}")

        # Check if all versions match
        if len(versions) > 1:
            first_version = next(iter(versions.values()))
            for file_name, version in versions.items():
                if version != first_version:
                    errors.append(
                        f"Version mismatch in {file_name}: {version} != {first_version}"
                    )

        return not bool(errors), errors


def main() -> None:
    """Main entry point for the script."""
    validator = VersionValidator()
    is_valid, errors = validator.validate_versions()

    if not is_valid:
        print("Version validation failed:")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)
    else:
        print("Version validation passed")
        sys.exit(0)


if __name__ == "__main__":
    main()
