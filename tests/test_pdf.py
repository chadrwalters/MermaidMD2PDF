"""Tests for the PDF generation component."""

from pathlib import Path

import pytest

from mermaidmd2pdf.pdf import PDFGenerator
from mermaidmd2pdf.processor import MermaidDiagram


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


def test_replace_diagrams_with_images(temp_output_dir: Path) -> None:
    """Test replacement of diagrams with image references."""
    diagram = MermaidDiagram(
        content="graph TD\nA-->B",
        start_line=1,
        end_line=2,
        original_text="```mermaid\ngraph TD\nA-->B\n```",
    )

    markdown = "# Test\n\n```mermaid\ngraph TD\nA-->B\n```\n\nMore text"
    diagram_images = {diagram: temp_output_dir / "diagram1.svg"}

    result = PDFGenerator._replace_diagrams_with_images(markdown, diagram_images)
    assert "```mermaid" not in result
    assert f"![Diagram]({diagram_images[diagram]})" in result
    assert "More text" in result


def test_replace_diagrams_with_images_multiple(temp_output_dir: Path) -> None:
    """Test replacement of multiple diagrams with image references."""
    diagram1 = MermaidDiagram(
        content="graph TD\nA-->B",
        start_line=1,
        end_line=2,
        original_text="```mermaid\ngraph TD\nA-->B\n```",
    )
    diagram2 = MermaidDiagram(
        content="sequenceDiagram\nA->>B: Hello",
        start_line=4,
        end_line=5,
        original_text="```mermaid\nsequenceDiagram\nA->>B: Hello\n```",
    )

    markdown = (
        "# Test\n\n"
        "```mermaid\ngraph TD\nA-->B\n```\n\n"
        "Middle text\n\n"
        "```mermaid\nsequenceDiagram\nA->>B: Hello\n```"
    )

    diagram_images = {
        diagram1: temp_output_dir / "diagram1.svg",
        diagram2: temp_output_dir / "diagram2.svg",
    }

    result = PDFGenerator._replace_diagrams_with_images(markdown, diagram_images)

    assert "```mermaid" not in result
    assert f"![Diagram]({diagram_images[diagram1]})" in result
    assert f"![Diagram]({diagram_images[diagram2]})" in result
    assert "Middle text" in result


def test_generate_pdf_success(temp_output_dir: Path) -> None:
    """Test successful PDF generation."""
    markdown_text = "# Test Document\n\nSome content"
    output_file = temp_output_dir / "test.pdf"
    diagram = MermaidDiagram(
        content="graph TD\nA-->B",
        start_line=1,
        end_line=2,
        original_text="```mermaid\ngraph TD\nA-->B\n```",
    )
    diagram_images = {diagram: temp_output_dir / "diagram1.svg"}

    success, error = PDFGenerator.generate_pdf(
        markdown_text, diagram_images, output_file, title="Test"
    )

    assert success
    assert error is None
    assert output_file.exists()
    assert output_file.suffix == ".pdf"


def test_generate_pdf_failure(temp_output_dir: Path) -> None:
    """Test PDF generation failure."""
    markdown_text = "# Test Document\n\nSome content"
    output_file = temp_output_dir / "test.pdf"
    diagram = MermaidDiagram(
        content="graph TD\nA-->B",
        start_line=1,
        end_line=2,
        original_text="```mermaid\ngraph TD\nA-->B\n```",
    )
    diagram_images = {diagram: temp_output_dir / "diagram1.svg"}

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("PATH", "")  # Make pandoc unavailable
        success, error = PDFGenerator.generate_pdf(
            markdown_text, diagram_images, output_file
        )

        assert not success
        assert error is not None
        assert "Failed to run Pandoc" in error


def test_generate_pdf_exception(temp_output_dir: Path) -> None:
    """Test PDF generation with exception."""
    markdown_text = "# Test Document\n\nSome content"
    output_file = temp_output_dir / "test.pdf"
    diagram = MermaidDiagram(
        content="graph TD\nA-->B",
        start_line=1,
        end_line=2,
        original_text="```mermaid\ngraph TD\nA-->B\n```",
    )
    diagram_images = {diagram: temp_output_dir / "diagram1.svg"}

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("PATH", "")  # Make pandoc unavailable
        success, error = PDFGenerator.generate_pdf(
            markdown_text, diagram_images, output_file
        )

        assert not success
        assert error is not None
        assert "Failed to run Pandoc" in error


def test_generate_pdf_cleanup(temp_output_dir: Path) -> None:
    """Test cleanup after PDF generation."""
    markdown_text = "# Test Document\n\nSome content"
    output_file = temp_output_dir / "test.pdf"
    diagram = MermaidDiagram(
        content="graph TD\nA-->B",
        start_line=1,
        end_line=2,
        original_text="```mermaid\ngraph TD\nA-->B\n```",
    )
    diagram_images = {diagram: temp_output_dir / "diagram1.svg"}

    success, error = PDFGenerator.generate_pdf(
        markdown_text, diagram_images, output_file
    )

    assert success
    assert error is None
    assert output_file.exists()

    # Verify temp file cleanup
    temp_files = list(temp_output_dir.glob("*.md"))
    assert not temp_files, "Temporary files should be cleaned up"
