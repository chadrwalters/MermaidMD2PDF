"""Integration tests for the MermaidMD2PDF package."""

from pathlib import Path

import pytest

from mermaidmd2pdf.cli import main
from mermaidmd2pdf.dependencies import DependencyChecker
from mermaidmd2pdf.generator import ImageGenerator
from mermaidmd2pdf.processor import MermaidProcessor
from mermaidmd2pdf.validator import FileValidator

# Constants
EXPECTED_SINGLE_DIAGRAM_COUNT = 1  # Test cases with a single diagram
EXPECTED_MULTIPLE_DIAGRAM_COUNT = 2  # Test cases with multiple diagrams
EXPECTED_ERROR_COUNT = 0  # Valid diagrams should produce no errors


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
    assert len(diagrams) == EXPECTED_SINGLE_DIAGRAM_COUNT

    # Generate images
    image_generator = ImageGenerator()
    diagram_images, errors = image_generator.generate_images(diagrams, temp_output_dir)
    assert not errors
    assert len(diagram_images) == EXPECTED_SINGLE_DIAGRAM_COUNT

    # Create PDF
    success = main.callback(
        str(sample_markdown), str(output_file), theme="light", debug=False
    )
    assert success is None  # Click commands return None on success
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
    is_valid, error = validator.validate_input_file(str(markdown_file))
    assert is_valid, f"Input validation failed: {error}"
    is_valid, error = validator.validate_output_file(str(output_file))
    assert is_valid, f"Output validation failed: {error}"

    # Read input file
    markdown_text = markdown_file.read_text()

    # Process markdown and extract diagrams
    processor = MermaidProcessor()
    processed_text, errors = processor.process_markdown(markdown_text)
    assert not errors, f"Markdown processing failed: {'; '.join(errors)}"

    diagrams = processor.extract_diagrams(markdown_text)
    assert len(diagrams) == EXPECTED_MULTIPLE_DIAGRAM_COUNT

    # Generate images
    image_generator = ImageGenerator()
    diagram_images, errors = image_generator.generate_images(diagrams, temp_output_dir)
    assert not errors, f"Failed to generate images: {'; '.join(errors)}"
    assert len(diagram_images) == EXPECTED_MULTIPLE_DIAGRAM_COUNT

    # Create PDF
    success = main.callback(
        str(markdown_file), str(output_file), theme="light", debug=False
    )
    assert success is None  # Click commands return None on success
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
    assert len(diagrams) == EXPECTED_ERROR_COUNT

    # Create PDF
    success = main.callback(
        str(markdown_file), str(output_file), theme="light", debug=False
    )
    assert success is None  # Click commands return None on success
    assert output_file.exists()
