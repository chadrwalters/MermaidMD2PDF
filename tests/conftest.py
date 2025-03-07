"""Test configuration and fixtures for MermaidMD2PDF."""

import subprocess
import tempfile
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture(scope="session", autouse=True)
def check_dependencies():
    """Check if required external dependencies are installed."""
    dependencies = ["pandoc", "mmdc"]
    missing = []

    for dep in dependencies:
        try:
            subprocess.run(
                [dep, "--version"],
                capture_output=True,
                check=True,
            )
        except (subprocess.CalledProcessError, FileNotFoundError):
            missing.append(dep)

    if missing:
        pytest.skip(
            f"Missing required dependencies: {', '.join(missing)}. "
            "Please install them before running tests."
        )


@pytest.fixture
def sample_markdown():
    """Create a sample markdown file with a Mermaid diagram."""
    content = """# Test Document

Here's a simple Mermaid diagram:

```mermaid
graph TD
    A[Start] --> B[Process]
    B --> C[End]
```

And some more text."""
    return content


@pytest.fixture
def sample_markdown_file(temp_dir, sample_markdown):
    """Create a temporary markdown file with sample content."""
    input_file = temp_dir / "test.md"
    input_file.write_text(sample_markdown)
    return input_file
