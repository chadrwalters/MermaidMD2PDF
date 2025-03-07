"""Tests for the image generator component."""

from pathlib import Path

import pytest

from mermaidmd2pdf.generator import ImageGenerator
from mermaidmd2pdf.processor import MermaidDiagram

# Test constants
EXPECTED_DIAGRAM_COUNT = 1
EXPECTED_ERROR_COUNT = 1
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


def test_create_mermaid_config() -> None:
    """Test creation of Mermaid configuration."""
    config = ImageGenerator._create_mermaid_config()
    assert config["theme"] == "default"
    assert "fontFamily" in config["themeVariables"]
    assert "fontSize" in config["themeVariables"]


def test_generate_image_success(temp_output_dir: Path) -> None:
    """Test successful image generation."""
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
    assert image_path.suffix == ".svg"


def test_generate_image_failure(temp_output_dir: Path) -> None:
    """Test image generation failure."""
    diagram = MermaidDiagram(
        content="invalid diagram",
        start_line=1,
        end_line=2,
        original_text="```mermaid\ninvalid diagram\n```",
    )

    success, error, image_path = ImageGenerator.generate_image(diagram, temp_output_dir)
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


def test_generate_images_success(temp_output_dir: Path) -> None:
    """Test successful image generation for multiple diagrams."""
    diagrams = [
        MermaidDiagram(
            content="graph TD\nA-->B",
            start_line=1,
            end_line=2,
            original_text="```mermaid\ngraph TD\nA-->B\n```",
        ),
        MermaidDiagram(
            content="sequenceDiagram\nA->>B: Hello",
            start_line=4,
            end_line=5,
            original_text="```mermaid\nsequenceDiagram\nA->>B: Hello\n```",
        ),
    ]

    diagram_images, errors = ImageGenerator.generate_images(diagrams, temp_output_dir)
    assert not errors
    assert len(diagram_images) == EXPECTED_DIAGRAM_COUNT
    assert all(isinstance(path, Path) for path in diagram_images.values())
    assert all(path.exists() for path in diagram_images.values())
    assert len(errors) == EXPECTED_ERROR_COUNT


def test_generate_images_failure(temp_output_dir: Path) -> None:
    """Test image generation failure for multiple diagrams."""
    diagrams = [
        MermaidDiagram(
            content="graph TD\nA-->B",
            start_line=1,
            end_line=2,
            original_text="```mermaid\ngraph TD\nA-->B\n```",
        ),
        MermaidDiagram(
            content="invalid diagram",
            start_line=4,
            end_line=5,
            original_text="```mermaid\ninvalid diagram\n```",
        ),
    ]

    diagram_images, errors = ImageGenerator.generate_images(diagrams, temp_output_dir)
    assert len(diagram_images) == 1
    assert len(errors) == 1
    assert "Failed to generate image for diagram at line 4" in errors[0]
    assert len(errors) == EXPECTED_ERROR_COUNT


def test_generate_images_exception(temp_output_dir: Path) -> None:
    """Test image generation with exception for multiple diagrams."""
    diagrams = [
        MermaidDiagram(
            content="graph TD\nA-->B",
            start_line=1,
            end_line=2,
            original_text="```mermaid\ngraph TD\nA-->B\n```",
        ),
    ]

    with pytest.MonkeyPatch.context() as mp:
        mp.setenv("PATH", "")  # Make mmdc unavailable
        diagram_images, errors = ImageGenerator.generate_images(
            diagrams, temp_output_dir
        )
        assert not diagram_images
        assert len(errors) == 1
        assert "Failed to generate image for diagram at line 1" in errors[0]
        assert len(errors) == EXPECTED_ERROR_COUNT


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
