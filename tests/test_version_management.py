"""Tests for version management functionality."""

import re
from pathlib import Path
from typing import Dict

import pytest
from packaging.version import Version

from scripts.update_changelog import ChangelogManager
from scripts.validate_version import VersionValidator


@pytest.fixture
def version_validator() -> VersionValidator:
    """Create a version validator instance."""
    return VersionValidator()


@pytest.fixture
def changelog_manager() -> ChangelogManager:
    """Create a changelog manager instance."""
    return ChangelogManager(Path("CHANGELOG.md"))


def test_version_validation(version_validator: VersionValidator) -> None:
    """Test version validation across files."""
    is_valid, errors = version_validator.validate_versions()
    assert is_valid, f"Version validation failed: {errors}"


def test_version_format(version_validator: VersionValidator) -> None:
    """Test that versions follow semantic versioning format."""
    versions: Dict[str, str] = {}

    # Get versions from all files
    for file_name, getter in version_validator.version_files.items():
        version = getter()
        assert version is not None, f"Could not find version in {file_name}"
        versions[file_name] = version

    # Check semantic version format
    for file_name, version in versions.items():
        try:
            Version(version)
        except ValueError as e:
            pytest.fail(f"Invalid semantic version in {file_name}: {version} - {e}")


def test_version_consistency(version_validator: VersionValidator) -> None:
    """Test that versions are consistent across files."""
    versions: Dict[str, str] = {}

    # Get versions from all files
    for file_name, getter in version_validator.version_files.items():
        version = getter()
        assert version is not None, f"Could not find version in {file_name}"
        versions[file_name] = version

    # Check version consistency
    if len(versions) > 1:
        first_version = next(iter(versions.values()))
        for file_name, version in versions.items():
            assert version == first_version, (
                f"Version mismatch in {file_name}: {version} != {first_version}"
            )


def test_changelog_format(changelog_manager: ChangelogManager) -> None:
    """Test that changelog follows Keep a Changelog format."""
    content = changelog_manager.changelog_path.read_text()

    # Check for required sections
    assert "## [Unreleased]" in content, "Missing [Unreleased] section"
    assert re.search(r"## \[\d+\.\d+\.\d+\]", content), "Missing version section"

    # Check section format
    sections = re.findall(
        r"### (Added|Changed|Deprecated|Removed|Fixed|Security)", content
    )
    assert sections, "No valid change type sections found"


def test_changelog_version_consistency(changelog_manager: ChangelogManager) -> None:
    """Test that changelog versions match current version."""
    current_version = changelog_manager.get_current_version()
    assert current_version is not None, "Could not get current version from changelog"

    # Get version from __init__.py
    init_version = VersionValidator()._get_init_version()
    assert init_version is not None, "Could not get version from __init__.py"

    # Compare versions
    assert str(current_version) == init_version, (
        "Changelog version does not match __init__.py version"
    )


def test_changelog_entry_creation(
    changelog_manager: ChangelogManager, tmp_path: Path
) -> None:
    """Test creating a new changelog entry."""
    # Create a temporary changelog for testing
    test_changelog = tmp_path / "CHANGELOG.md"
    test_changelog.write_text(
        "# Changelog\n\n## [Unreleased]\n\n### Added\n- Initial test\n"
    )

    # Create a new changelog manager with the test file
    test_manager = ChangelogManager(test_changelog)

    # Add a new entry
    changes = {
        "Added": ["New feature"],
        "Fixed": ["Bug fix"],
    }
    test_manager.add_entry("1.0.0", changes)

    # Verify the entry was added correctly
    content = test_changelog.read_text()
    assert "## [1.0.0]" in content, "Version entry not added"
    assert "### Added" in content, "Added section not present"
    assert "### Fixed" in content, "Fixed section not present"
    assert "- New feature" in content, "New feature not added"
    assert "- Bug fix" in content, "Bug fix not added"


def test_get_unreleased_changes(changelog_manager: ChangelogManager) -> None:
    """Test getting unreleased changes from changelog."""
    changes = changelog_manager.get_unreleased_changes()

    # Verify the structure
    assert isinstance(changes, dict), "Changes should be a dictionary"
    assert all(isinstance(items, list) for items in changes.values()), (
        "All change types should be lists"
    )

    # Verify change types
    expected_types = {"Added", "Changed", "Deprecated", "Removed", "Fixed", "Security"}
    assert set(changes.keys()) == expected_types, "Missing expected change types"
