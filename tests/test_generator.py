"""Tests for the image generator component."""

import io
from pathlib import Path
from typing import List
from unittest.mock import patch

import pytest

from mermaidmd2pdf.generator import ImageGenerator
from mermaidmd2pdf.processor import MermaidDiagram

# Test constants
EXPECTED_SINGLE_DIAGRAM_COUNT = 1  # Test cases with a single diagram
EXPECTED_MULTIPLE_DIAGRAM_COUNT = 2  # Test cases with multiple diagrams
EXPECTED_ERROR_COUNT = 0  # No errors expected for valid diagrams
EXPECTED_FAILURE_ERROR_COUNT = 1  # One error expected for invalid diagrams
EXPECTED_LINE_NUMBER = 4


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
    """Create multiple sample Mermaid diagrams for testing."""
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


def test_create_mermaid_config() -> None:
    """Test creation of Mermaid configuration."""
    config = ImageGenerator._create_mermaid_config()
    assert config["theme"] == "default"
    assert "fontFamily" in config["themeVariables"]
    assert "fontSize" in config["themeVariables"]


def test_generate_image_success(
    temp_output_dir: Path, sample_diagram: MermaidDiagram
) -> None:
    """Test successful image generation."""
    success, error, image_path = ImageGenerator.generate_image(
        sample_diagram, temp_output_dir
    )
    assert success
    assert error is None
    assert image_path is not None
    assert image_path.exists()
    assert image_path.suffix == ".png"


def test_generate_image_failure(temp_output_dir: Path) -> None:
    """Test image generation failure."""
    invalid_diagram = MermaidDiagram(
        content="invalid diagram",
        start_line=1,
        end_line=2,
        original_text="```mermaid\ninvalid diagram\n```",
    )
    success, error, image_path = ImageGenerator.generate_image(
        invalid_diagram, temp_output_dir
    )
    assert not success
    assert error is not None
    assert image_path is None


def test_generate_image_exception(temp_output_dir: Path) -> None:
    """Test image generation with exception."""
    diagram = MermaidDiagram(
        content="graph TD\nA-->B",
        start_line=1,
        end_line=2,
        original_text="```mermaid\ngraph TD\nA-->B\n```",
    )

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("PATH", "")  # Make mmdc unavailable
        success, error, image_path = ImageGenerator.generate_image(
            diagram, temp_output_dir
        )
        assert not success
        assert error is not None
        assert image_path is None


def test_generate_images_success(
    temp_output_dir: Path, multiple_diagrams: List[MermaidDiagram]
) -> None:
    """Test successful generation of multiple images."""
    with patch("sys.stdout", new=io.StringIO()) as fake_output:
        diagram_images, errors = ImageGenerator.generate_images(
            multiple_diagrams, temp_output_dir
        )
        output = fake_output.getvalue()

    assert len(diagram_images) == len(multiple_diagrams)
    assert not errors
    assert "🔄 Processing 2 Mermaid diagrams..." in output
    assert "✅ Generated diagram 1/2" in output
    assert "✅ Generated diagram 2/2" in output
    assert "✨ Successfully generated 2/2 diagrams" in output


def test_generate_images_partial_failure(
    temp_output_dir: Path, multiple_diagrams: List[MermaidDiagram]
) -> None:
    """Test partial failure in generating multiple images."""
    # Add an invalid diagram to the list
    invalid_diagram = MermaidDiagram(
        content="invalid diagram",
        start_line=10,
        end_line=11,
        original_text="```mermaid\ninvalid diagram\n```",
    )
    diagrams = [*multiple_diagrams, invalid_diagram]

    with patch("sys.stdout", new=io.StringIO()) as fake_output:
        diagram_images, errors = ImageGenerator.generate_images(
            diagrams, temp_output_dir
        )
        output = fake_output.getvalue()

    assert len(diagram_images) == len(multiple_diagrams)
    assert len(errors) == 1
    assert "🔄 Processing 3 Mermaid diagrams..." in output
    assert "❌ Failed to generate diagram" in output
    assert "⚠️  Failed to generate 1 diagram" in output


def test_generate_images_empty_list(temp_output_dir: Path) -> None:
    """Test handling of empty diagram list."""
    with patch("sys.stdout", new=io.StringIO()) as fake_output:
        diagram_images, errors = ImageGenerator.generate_images([], temp_output_dir)
        output = fake_output.getvalue()

    assert not diagram_images
    assert not errors
    assert output.strip() == ""  # No output for empty list


def test_generate_images_with_warnings(
    temp_output_dir: Path, sample_diagram: MermaidDiagram
) -> None:
    """Test handling of warnings during image generation."""
    # Modify diagram to trigger a warning but not an error
    diagram = MermaidDiagram(
        content=(
            "graph TD\n"
            "A[Start] --> B[End]\n"
            "C[Orphan]"  # Orphan node will trigger a warning
        ),
        start_line=1,
        end_line=3,
        original_text="```mermaid\ngraph TD\nA[Start] --> B[End]\nC[Orphan]\n```",
    )

    with patch("sys.stdout", new=io.StringIO()) as fake_output:
        diagram_images, errors = ImageGenerator.generate_images(
            [diagram], temp_output_dir
        )
        output = fake_output.getvalue()

    assert len(diagram_images) == 1
    assert not errors
    assert "🔄 Processing 1 Mermaid diagram..." in output
    assert "✅ Generated diagram 1/1" in output
    assert "✨ Successfully generated 1/1 diagrams" in output


def test_generate_images_cleanup(temp_output_dir: Path) -> None:
    """Test cleanup after image generation."""
    diagram = MermaidDiagram(
        content="graph TD\nA-->B",
        start_line=1,
        end_line=2,
        original_text="```mermaid\ngraph TD\nA-->B\n```",
    )

    success, error, image_path = ImageGenerator.generate_image(diagram, temp_output_dir)
    assert success
    assert error is None
    assert image_path is not None
    assert image_path.exists()

    # Verify temp file cleanup
    temp_files = list(temp_output_dir.glob("*.mmd"))
    assert not temp_files, "Temporary files should be cleaned up"
