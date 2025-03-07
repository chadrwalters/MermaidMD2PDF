"""Common test fixtures and utilities."""

import shutil
import tempfile
from pathlib import Path
from typing import Generator

import pytest

from mermaidmd2pdf.processor import MermaidDiagram


def check_dependencies() -> None:
    """Check if all required external dependencies are available."""
    # Check for mmdc (Mermaid CLI)
    if shutil.which("mmdc") is None:
        pytest.skip(
            "Mermaid CLI (mmdc) not found. Please install with: "
            "npm install -g @mermaid-js/mermaid-cli"
        )

    # Check for pandoc
    if shutil.which("pandoc") is None:
        pytest.skip(
            "Pandoc not found. Please install with: "
            "brew install pandoc (macOS) or "
            "apt-get install pandoc (Linux)"
        )


@pytest.fixture(autouse=True)
def ensure_dependencies() -> None:
    """Ensure all required dependencies are available before running tests."""
    check_dependencies()


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_diagram() -> MermaidDiagram:
    """Create a sample Mermaid diagram for testing."""
    return MermaidDiagram(
        content="graph TD\nA[Start] --> B[End]",
        start_line=1,
        end_line=3,
        original_text="```mermaid\ngraph TD\nA[Start] --> B[End]\n```",
    )


@pytest.fixture
def sample_markdown() -> str:
    """Create a sample markdown file with a Mermaid diagram."""
    return """# Test Document

This is a test document with a Mermaid diagram:

```mermaid
graph TD
    A[Start] --> B[Process]
    B --> C[End]
```

And some more text after the diagram."""


@pytest.fixture
def sample_markdown_file(temp_dir: Path, sample_markdown: str) -> Path:
    """Create a temporary markdown file with sample content."""
    input_file = temp_dir / "test.md"
    input_file.write_text(sample_markdown)
    return input_file
