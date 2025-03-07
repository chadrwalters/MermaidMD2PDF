"""Integration tests for the MermaidMD2PDF package."""

from pathlib import Path

import pytest
from mermaidmd2pdf.cli import main
from mermaidmd2pdf.dependencies import DependencyChecker
from mermaidmd2pdf.generator import ImageGenerator
from mermaidmd2pdf.processor import MermaidProcessor
from mermaidmd2pdf.validator import FileValidator

# Constants
EXPECTED_DIAGRAM_COUNT = 2


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def sample_markdown(tmp_path: Path) -> Path:
    """Create a sample markdown file with a Mermaid diagram."""
    markdown_file = tmp_path / "test.md"
    markdown_file.write_text(
        """# Test Document

```mermaid
graph TD
A[Start] --> B[End]
```

Some text here.
"""
    )
    return markdown_file


def test_workflow_with_single_diagram(
    temp_output_dir: Path, sample_markdown: Path
) -> None:
    """Test the complete workflow with a single diagram."""
    # Check dependencies
    checker = DependencyChecker()
    deps_ok, error = checker.verify_all()
    assert deps_ok, f"Dependencies not satisfied: {error}"

    # Validate input and output files
    validator = FileValidator()
    output_file = temp_output_dir / "output.pdf"
    assert validator.validate_input_file(str(sample_markdown))
    assert validator.validate_output_file(str(output_file))

    # Read input file
    markdown_text = sample_markdown.read_text()

    # Process markdown and extract diagrams
    processor = MermaidProcessor()
    diagrams = processor.extract_diagrams(markdown_text)
    assert len(diagrams) == 1

    # Generate images
    image_generator = ImageGenerator()
    diagram_images, errors = image_generator.generate_images(diagrams, temp_output_dir)
    assert not errors
    assert len(diagram_images) == 1

    # Create PDF
    success = main(str(sample_markdown), str(output_file))
    assert success
    assert output_file.exists()


def test_workflow_with_multiple_diagrams(temp_output_dir: Path) -> None:
    """Test the complete workflow with multiple diagrams."""
    # Create markdown file with multiple diagrams
    markdown_file = temp_output_dir / "test.md"
    markdown_file.write_text(
        """# Test Document

```mermaid
graph TD
A[Start] --> B[Process]
B --> C[End]
```

Some text between diagrams.

```mermaid
sequenceDiagram
    participant A
    participant B
    A->>B: Hello
    B->>A: Hi there!
```

Final text.
"""
    )

    # Check dependencies
    checker = DependencyChecker()
    deps_ok, error = checker.verify_all()
    assert deps_ok, f"Dependencies not satisfied: {error}"

    # Validate input and output files
    validator = FileValidator()
    output_file = temp_output_dir / "output.pdf"
    assert validator.validate_input_file(str(markdown_file))
    assert validator.validate_output_file(str(output_file))

    # Read input file
    markdown_text = markdown_file.read_text()

    # Process markdown and extract diagrams
    processor = MermaidProcessor()
    diagrams = processor.extract_diagrams(markdown_text)
    assert len(diagrams) == EXPECTED_DIAGRAM_COUNT

    # Generate images
    image_generator = ImageGenerator()
    diagram_images, errors = image_generator.generate_images(diagrams, temp_output_dir)
    assert not errors
    assert len(diagram_images) == EXPECTED_DIAGRAM_COUNT

    # Create PDF
    success = main(str(markdown_file), str(output_file))
    assert success
    assert output_file.exists()


def test_workflow_with_no_diagrams(temp_output_dir: Path) -> None:
    """Test the complete workflow with a markdown file containing no diagrams."""
    # Create markdown file without diagrams
    markdown_file = temp_output_dir / "test.md"
    markdown_file.write_text(
        """# Test Document

This is a test document with no Mermaid diagrams.

Just some regular markdown text.
"""
    )

    # Check dependencies
    checker = DependencyChecker()
    deps_ok, error = checker.verify_all()
    assert deps_ok, f"Dependencies not satisfied: {error}"

    # Validate input and output files
    validator = FileValidator()
    output_file = temp_output_dir / "output.pdf"
    assert validator.validate_input_file(str(markdown_file))
    assert validator.validate_output_file(str(output_file))

    # Read input file
    markdown_text = markdown_file.read_text()

    # Process markdown and extract diagrams
    processor = MermaidProcessor()
    diagrams = processor.extract_diagrams(markdown_text)
    assert len(diagrams) == 0

    # Create PDF
    success = main(str(markdown_file), str(output_file))
    assert success
    assert output_file.exists()
