import os
import tempfile
from pathlib import Path
import pytest
from mermaidmd2pdf.validator import FileValidator
from mermaidmd2pdf.dependencies import DependencyChecker
from mermaidmd2pdf.processor import MermaidProcessor
from mermaidmd2pdf.generator import ImageGenerator
from mermaidmd2pdf.pdf import PDFGenerator

@pytest.fixture
def temp_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture
def sample_markdown():
    return """# Test Document

This is a test document with a Mermaid diagram:

```mermaid
graph TD
    A[Start] --> B[Process]
    B --> C[End]
```

And some more text after the diagram."""

def test_complete_workflow(temp_dir, sample_markdown):
    # Set up input and output files
    input_file = temp_dir / "test.md"
    output_file = temp_dir / "test.pdf"

    # Write sample markdown to input file
    input_file.write_text(sample_markdown)

    # Step 1: Validate files
    validator = FileValidator()
    assert validator.validate_input_file(input_file)
    assert validator.validate_output_file(output_file)

    # Step 2: Check dependencies
    checker = DependencyChecker()
    is_satisfied, error = checker.verify_all()
    assert is_satisfied, f"Dependencies not satisfied: {error}"

    # Step 3: Process Mermaid diagrams
    processor = MermaidProcessor()
    diagrams = processor.extract_diagrams(input_file.read_text())
    assert len(diagrams) == 1

    # Step 4: Generate images
    image_generator = ImageGenerator()
    image_paths = []
    for diagram in diagrams:
        image_path = temp_dir / f"diagram_{diagram.start_line}.png"
        success, error, path = image_generator.generate_image(diagram, temp_dir)
        assert success and path is not None, f"Image generation failed: {error}"
        image_paths.append(path)

    # Step 5: Generate PDF
    pdf_generator = PDFGenerator()
    success, error = pdf_generator.generate_pdf(
        input_file.read_text(),
        dict(zip(diagrams, image_paths)),
        output_file
    )
    assert success, f"PDF generation failed: {error}"

    # Verify PDF was created
    assert output_file.exists()
    assert output_file.stat().st_size > 0

def test_workflow_with_multiple_diagrams(temp_dir):
    markdown_content = """# Multiple Diagrams

First diagram:

```mermaid
graph TD
    A[Start] --> B[Middle]
    B --> C[End]
```

Second diagram:

```mermaid
sequenceDiagram
    Alice->>John: Hello John
    John-->>Alice: Hi Alice
```
"""
    # Set up files
    input_file = temp_dir / "multiple.md"
    output_file = temp_dir / "multiple.pdf"
    input_file.write_text(markdown_content)

    # Run complete workflow
    validator = FileValidator()
    assert validator.validate_input_file(input_file)
    assert validator.validate_output_file(output_file)

    checker = DependencyChecker()
    is_satisfied, error = checker.verify_all()
    assert is_satisfied, f"Dependencies not satisfied: {error}"

    processor = MermaidProcessor()
    diagrams = processor.extract_diagrams(input_file.read_text())
    assert len(diagrams) == 2

    image_generator = ImageGenerator()
    image_paths = []
    for diagram in diagrams:
        image_path = temp_dir / f"diagram_{diagram.start_line}.png"
        success, error, path = image_generator.generate_image(diagram, temp_dir)
        assert success and path is not None, f"Image generation failed: {error}"
        image_paths.append(path)

    pdf_generator = PDFGenerator()
    success, error = pdf_generator.generate_pdf(
        input_file.read_text(),
        dict(zip(diagrams, image_paths)),
        output_file
    )
    assert success, f"PDF generation failed: {error}"

    assert output_file.exists()
    assert output_file.stat().st_size > 0

def test_workflow_error_handling(temp_dir):
    # Test with invalid Mermaid syntax
    invalid_markdown = """# Invalid Diagram

```mermaid
graph TD
    A[Start] --> [Invalid]
```
"""
    input_file = temp_dir / "invalid.md"
    output_file = temp_dir / "invalid.pdf"
    input_file.write_text(invalid_markdown)

    validator = FileValidator()
    assert validator.validate_input_file(input_file)

    processor = MermaidProcessor()
    diagrams = processor.extract_diagrams(input_file.read_text())
    assert len(diagrams) == 1

    image_generator = ImageGenerator()
    success, error, _ = image_generator.generate_image(diagrams[0], temp_dir)
    assert not success, "Expected image generation to fail with invalid diagram"
    assert error is not None, "Expected error message for invalid diagram"
