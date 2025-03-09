"""Tests for the PDF generation component."""

import io
import subprocess
import types
from pathlib import Path
from typing import Any, Dict, List, Optional, Type
from unittest.mock import patch

import pytest

from mermaidmd2pdf.generator import PDFGenerator
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


@pytest.fixture
def multiple_diagrams() -> List[MermaidDiagram]:
    """Create a list of test diagrams."""
    return [
        MermaidDiagram(
            content="graph TD\nA[Start] --> B[End]",
            start_line=1,
            end_line=3,
            original_text="```mermaid\ngraph TD\nA[Start] --> B[End]\n```",
        ),
        MermaidDiagram(
            content="sequenceDiagram\nA->>B: Hello",
            start_line=5,
            end_line=7,
            original_text="```mermaid\nsequenceDiagram\nA->>B: Hello\n```",
        ),
    ]


def test_generate_pdf_success(
    temp_output_dir: Path, multiple_diagrams: List[MermaidDiagram]
) -> None:
    """Test successful PDF generation with proper output messages."""
    markdown_text = "# Test Document\n\nSome content"
    output_path = temp_output_dir / "output.pdf"

    # Create diagram images dictionary
    diagram_images = {}
    for i, diagram in enumerate(multiple_diagrams):
        image_path = temp_output_dir / f"diagram_{i}.png"
        image_path.write_text("dummy image")
        diagram_images[diagram] = image_path

    def mock_run(
        cmd: List[str], **kwargs: Dict[str, Any]
    ) -> subprocess.CompletedProcess[str]:
        if cmd[0] == "pandoc":
            # Create a dummy PDF file
            output_path.write_text("dummy pdf")
            return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

    with patch("sys.stdout", new=io.StringIO()) as fake_output, patch(
        "subprocess.run", side_effect=mock_run
    ):
        success, error = PDFGenerator.generate_pdf(
            markdown_text, diagram_images, output_path, title="Test Document"
        )
        fake_output.getvalue()

    assert success
    assert error is None
    assert output_path.exists()


def test_generate_pdf_image_failure(temp_output_dir: Path) -> None:
    """Test PDF generation with image generation failure."""
    markdown_text = "# Test Document\n\nSome content"
    output_path = temp_output_dir / "output.pdf"

    invalid_diagram = MermaidDiagram(
        content="invalid diagram",
        start_line=1,
        end_line=2,
        original_text="```mermaid\ninvalid diagram\n```",
    )

    # Create diagram images dictionary
    diagram_images = {invalid_diagram: temp_output_dir / "invalid_diagram.png"}

    def mock_run(
        cmd: List[str], **kwargs: Dict[str, Any]
    ) -> subprocess.CompletedProcess[str]:
        if cmd[0] == "pandoc":
            return subprocess.CompletedProcess(
                cmd, returncode=1, stdout="", stderr="Invalid diagram"
            )
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

    with patch("sys.stdout", new=io.StringIO()) as fake_output, patch(
        "subprocess.run", side_effect=mock_run
    ):
        success, error = PDFGenerator.generate_pdf(
            markdown_text, diagram_images, output_path, title="Test Document"
        )
        fake_output.getvalue()

    assert not success
    assert error is not None
    assert "Invalid diagram" in error


def test_generate_pdf_pandoc_failure(
    temp_output_dir: Path, multiple_diagrams: List[MermaidDiagram]
) -> None:
    """Test PDF generation with Pandoc failure."""
    markdown_text = "# Test Document\n\nSome content"
    output_path = temp_output_dir / "output.pdf"

    # Create diagram images dictionary
    diagram_images = {}
    for i, diagram in enumerate(multiple_diagrams):
        image_path = temp_output_dir / f"diagram_{i}.png"
        image_path.write_text("dummy image")
        diagram_images[diagram] = image_path

    def mock_run(
        cmd: List[str], **kwargs: Dict[str, Any]
    ) -> subprocess.CompletedProcess[str]:
        if cmd[0] == "pandoc":
            return subprocess.CompletedProcess(
                cmd, returncode=1, stdout="", stderr="Pandoc error"
            )
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

    with patch("sys.stdout", new=io.StringIO()) as fake_output, patch(
        "subprocess.run", side_effect=mock_run
    ):
        success, error = PDFGenerator.generate_pdf(
            markdown_text, diagram_images, output_path, title="Test Document"
        )
        fake_output.getvalue()

    assert not success
    assert error is not None
    assert "Pandoc error" in error


def test_generate_pdf_cleanup(
    temp_output_dir: Path, multiple_diagrams: List[MermaidDiagram]
) -> None:
    """Test cleanup after PDF generation."""
    markdown_text = "# Test Document\n\nSome content"
    output_path = temp_output_dir / "output.pdf"

    # Create diagram images dictionary
    diagram_images = {}
    for i, diagram in enumerate(multiple_diagrams):
        image_path = temp_output_dir / f"diagram_{i}.png"
        image_path.write_text("dummy image")
        diagram_images[diagram] = image_path

    def mock_run(
        cmd: List[str], **kwargs: Dict[str, Any]
    ) -> subprocess.CompletedProcess[str]:
        if cmd[0] == "pandoc":
            # Create a dummy PDF file
            output_path.write_text("dummy pdf")
            return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

    # Create a mock temporary file
    mock_temp_path = temp_output_dir / "temp.md"

    class MockTempFile:
        """Mock implementation of NamedTemporaryFile."""

        def __init__(self, *args: Any, **kwargs: Any) -> None:
            self.name = str(mock_temp_path)

        def __enter__(self) -> "MockTempFile":
            # Create the file when entering the context
            mock_temp_path.write_text("")
            return self

        def __exit__(
            self,
            exc_type: Optional[Type[BaseException]],
            exc_val: Optional[BaseException],
            exc_tb: Optional[types.TracebackType],
        ) -> None:
            # Clean up the file when exiting the context
            if mock_temp_path.exists():
                mock_temp_path.unlink()

        def write(self, content: str) -> None:
            # Write content to the file
            mock_temp_path.write_text(content)

        def flush(self) -> None:
            # No need to do anything for flush in our mock
            pass

        def close(self) -> None:
            # Clean up the file when closing
            if mock_temp_path.exists():
                mock_temp_path.unlink()

    with patch("sys.stdout", new=io.StringIO()), patch(
        "subprocess.run", side_effect=mock_run
    ), patch("tempfile.NamedTemporaryFile", MockTempFile):
        success, error = PDFGenerator.generate_pdf(
            markdown_text, diagram_images, output_path, title="Test Document"
        )

    assert success
    assert error is None
    assert output_path.exists()

    # Verify temp file cleanup
    assert not mock_temp_path.exists(), "Temporary markdown file should be cleaned up"


def test_generate_pdf_no_diagrams(temp_output_dir: Path) -> None:
    """Test PDF generation with no diagrams."""
    markdown_text = "# Test Document\n\nSome content"
    output_path = temp_output_dir / "output.pdf"

    def mock_run(
        cmd: List[str], **kwargs: Dict[str, Any]
    ) -> subprocess.CompletedProcess[str]:
        if cmd[0] == "pandoc":
            # Create a dummy PDF file
            output_path.write_text("dummy pdf")
            return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")
        return subprocess.CompletedProcess(cmd, returncode=0, stdout="", stderr="")

    with patch("sys.stdout", new=io.StringIO()) as fake_output, patch(
        "subprocess.run", side_effect=mock_run
    ):
        success, error = PDFGenerator.generate_pdf(
            markdown_text, {}, output_path, title="Test Document"
        )
        fake_output.getvalue()

    assert success
    assert error is None
    assert output_path.exists()
