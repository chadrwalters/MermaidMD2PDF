#!/usr/bin/env python3
"""Script to update CHANGELOG.md following Keep a Changelog format."""

import argparse
import re
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

from packaging.version import Version


class ChangelogManager:
    """Manages the CHANGELOG.md file following Keep a Changelog format."""

    def __init__(self, changelog_path: Path):
        """Initialize the changelog manager.

        Args:
            changelog_path: Path to the CHANGELOG.md file
        """
        self.changelog_path = changelog_path
        self.content = self.changelog_path.read_text()

    def get_current_version(self) -> Optional[Version]:
        """Get the current version from the changelog.

        Returns:
            Current version or None if not found
        """
        version_pattern = r"## \[(\d+\.\d+\.\d+)\]"
        match = re.search(version_pattern, self.content)
        if match:
            return Version(match.group(1))
        return None

    def add_entry(self, version: str, changes: Dict[str, List[str]]) -> None:
        """Add a new changelog entry."""
        content = self.changelog_path.read_text()
        lines = content.splitlines()
        new_lines = []
        added = False

        for current_line in lines:
            if current_line.startswith("## [Unreleased]") and not added:
                new_lines.append(current_line)
                new_lines.append("")
                new_lines.append(
                    f"## [{version}] - {datetime.now().strftime('%Y-%m-%d')}"
                )
                new_lines.append("")
                for change_type, items in changes.items():
                    new_lines.append(f"### {change_type}")
                    for item in items:
                        new_lines.append(f"- {item}")
                    new_lines.append("")
                added = True
            else:
                new_lines.append(current_line)

        self.changelog_path.write_text("\n".join(new_lines))

    def get_unreleased_changes(self) -> Dict[str, List[str]]:
        """Get all unreleased changes from the changelog."""
        changes: Dict[str, List[str]] = {
            "Added": [],
            "Changed": [],
            "Deprecated": [],
            "Removed": [],
            "Fixed": [],
            "Security": [],
        }

        content = self.changelog_path.read_text()
        lines = content.splitlines()
        current_section = None

        for current_line in lines:
            if current_line.startswith("## [Unreleased]"):
                current_section = "Unreleased"
            elif current_line.startswith("### "):
                change_type = current_line[4:].strip()
                if change_type in changes:
                    current_section = change_type
                else:
                    current_section = None
            elif current_line.startswith("- ") and current_section in changes:
                changes[current_section].append(current_line[2:].strip())

        return changes


def main() -> None:
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(description="Update CHANGELOG.md")
    parser.add_argument(
        "--version",
        required=True,
        help="Version number (e.g., 1.0.0)",
    )
    parser.add_argument(
        "--date",
        help="Release date in YYYY-MM-DD format (default: today)",
    )
    parser.add_argument(
        "--add",
        action="append",
        help="Add a change entry (format: type:description)",
    )
    parser.add_argument(
        "--get-unreleased",
        action="store_true",
        help="Get all unreleased changes",
    )

    args = parser.parse_args()

    changelog_path = Path("CHANGELOG.md")
    manager = ChangelogManager(changelog_path)

    if args.get_unreleased:
        changes = manager.get_unreleased_changes()
        for change_type, items in changes.items():
            if items:
                print(f"\n{change_type}:")
                for item in items:
                    print(f"- {item}")
        return

    if args.add:
        change_entries: Dict[str, List[str]] = {
            "Added": [],
            "Changed": [],
            "Deprecated": [],
            "Removed": [],
            "Fixed": [],
            "Security": [],
        }

        for entry in args.add:
            try:
                change_type, description = entry.split(":", 1)
                if change_type in change_entries:
                    change_entries[change_type].append(description.strip())
                else:
                    print(f"Warning: Unknown change type '{change_type}'")
            except ValueError:
                print(f"Warning: Invalid entry format '{entry}'")

        manager.add_entry(args.version, change_entries)


if __name__ == "__main__":
    main()
