"""Tests for the PDF generator component."""
import os
import subprocess
from pathlib import Path
from unittest.mock import ANY, patch

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


def test_replace_diagrams_with_images(temp_output_dir: Path, sample_diagram: MermaidDiagram):
    """Test replacement of diagrams with image references."""
    markdown = "# Test\n\n```mermaid\ngraph TD\nA[Start] --> B[End]\n```\n\nMore text"
    image_path = temp_output_dir / "diagram.svg"
    diagram_images = {sample_diagram: image_path}

    result = PDFGenerator._replace_diagrams_with_images(markdown, diagram_images)

    assert "```mermaid" not in result
    assert f"![Diagram]({image_path})" in result
    assert "# Test" in result
    assert "More text" in result


def test_replace_diagrams_with_images_multiple(temp_output_dir: Path):
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


def test_generate_pdf_success(temp_output_dir: Path, sample_diagram: MermaidDiagram):
    """Test successful PDF generation."""
    markdown = "# Test\n\n```mermaid\ngraph TD\nA[Start] --> B[End]\n```"
    output_file = temp_output_dir / "output.pdf"
    diagram_images = {sample_diagram: temp_output_dir / "diagram.svg"}

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0

        success, error = PDFGenerator.generate_pdf(
            markdown, diagram_images, output_file, title="Test Document"
        )

        assert success
        assert error is None

        # Verify Pandoc command
        mock_run.assert_called_once()
        args = mock_run.call_args[0][0]
        assert args[0] == "pandoc"
        assert args[2] == "-o"
        assert args[3] == str(output_file)
        assert "--pdf-engine=weasyprint" in args
        assert "--standalone" in args


def test_generate_pdf_failure(temp_output_dir: Path, sample_diagram: MermaidDiagram):
    """Test PDF generation failure."""
    markdown = "# Test\n\n```mermaid\ngraph TD\nA[Start] --> B[End]\n```"
    output_file = temp_output_dir / "output.pdf"
    diagram_images = {sample_diagram: temp_output_dir / "diagram.svg"}

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Pandoc error"

        success, error = PDFGenerator.generate_pdf(markdown, diagram_images, output_file)

        assert not success
        assert "Pandoc error" in error


def test_generate_pdf_exception(temp_output_dir: Path, sample_diagram: MermaidDiagram):
    """Test PDF generation with exception."""
    markdown = "# Test\n\n```mermaid\ngraph TD\nA[Start] --> B[End]\n```"
    output_file = temp_output_dir / "output.pdf"
    diagram_images = {sample_diagram: temp_output_dir / "diagram.svg"}

    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "pandoc")

        success, error = PDFGenerator.generate_pdf(markdown, diagram_images, output_file)

        assert not success
        assert "Failed to run Pandoc" in error


def test_generate_pdf_cleanup(temp_output_dir: Path, sample_diagram: MermaidDiagram):
    """Test temporary file cleanup after PDF generation."""
    markdown = "# Test\n\n```mermaid\ngraph TD\nA[Start] --> B[End]\n```"
    output_file = temp_output_dir / "output.pdf"
    diagram_images = {sample_diagram: temp_output_dir / "diagram.svg"}

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0

        PDFGenerator.generate_pdf(markdown, diagram_images, output_file)

        # Check that no temporary .md files are left
        temp_files = list(temp_output_dir.glob("*.md"))
        assert not temp_files
