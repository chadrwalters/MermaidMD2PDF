"""Tests for the image generator component."""

import subprocess
from pathlib import Path
from unittest.mock import ANY, patch

import pytest
from mermaidmd2pdf.generator import ImageGenerator
from mermaidmd2pdf.processor import MermaidDiagram

# Test constants
EXPECTED_DIAGRAM_COUNT = 2
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


def test_create_mermaid_config():
    """Test creation of Mermaid configuration."""
    config = ImageGenerator._create_mermaid_config()
    assert config["theme"] == "default"
    assert "fontFamily" in config["themeVariables"]
    assert "fontSize" in config["themeVariables"]


def test_generate_image_success(temp_output_dir: Path, sample_diagram: MermaidDiagram):
    """Test successful image generation."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0

        success, error, image_path = ImageGenerator.generate_image(
            sample_diagram, temp_output_dir
        )

        assert success
        assert error is None
        assert image_path is not None
        assert image_path.parent == temp_output_dir
        assert image_path.suffix == ".svg"

        # Verify subprocess call
        mock_run.assert_called_once_with(
            ["mmdc", "-i", ANY, "-o", str(image_path), "-c", ANY],
            capture_output=True,
            text=True,
        )


def test_generate_image_failure(temp_output_dir: Path, sample_diagram: MermaidDiagram):
    """Test image generation failure."""
    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 1
        mock_run.return_value.stderr = "Mermaid CLI error"

        success, error, image_path = ImageGenerator.generate_image(
            sample_diagram, temp_output_dir
        )

        assert not success
        assert "Mermaid CLI error" in error
        assert image_path is None


def test_generate_image_exception(
    temp_output_dir: Path, sample_diagram: MermaidDiagram
):
    """Test image generation with exception."""
    with patch("subprocess.run") as mock_run:
        mock_run.side_effect = subprocess.CalledProcessError(1, "mmdc")

        success, error, image_path = ImageGenerator.generate_image(
            sample_diagram, temp_output_dir
        )

        assert not success
        assert "Failed to run Mermaid CLI" in error
        assert image_path is None


def test_generate_images_all_success(temp_output_dir: Path):
    """Test generation of multiple images with all successes."""
    diagrams = [
        MermaidDiagram("graph TD\nA-->B", 1, 2, ""),
        MermaidDiagram("sequenceDiagram\nA->>B: Hello", 3, 4, ""),
    ]

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0

        diagram_images, errors = ImageGenerator.generate_images(
            diagrams, temp_output_dir
        )

        assert len(diagram_images) == EXPECTED_DIAGRAM_COUNT
        assert not errors
        assert mock_run.call_count == EXPECTED_DIAGRAM_COUNT


def test_generate_images_mixed_results(temp_output_dir: Path):
    """Test generation of multiple images with mixed results."""
    valid_diagram = MermaidDiagram("graph TD\nA-->B", 1, 2, "")
    invalid_diagram = MermaidDiagram("invalid", 3, 4, "")
    diagrams = [valid_diagram, invalid_diagram]

    def mock_run_side_effect(args, **kwargs):
        # Create a mock result
        result = subprocess.CompletedProcess(args, 0)
        result.stderr = ""

        # Check if this is the invalid diagram by comparing file paths
        if str(temp_output_dir / f"diagram_{hash('invalid')}.svg") in args[4]:
            result.returncode = 1
            result.stderr = "Invalid diagram"

        return result

    with patch("subprocess.run", side_effect=mock_run_side_effect):
        diagram_images, errors = ImageGenerator.generate_images(
            diagrams, temp_output_dir
        )

        assert len(diagram_images) == 1
        assert len(errors) == 1
        assert "Invalid diagram" in errors[0]
        assert valid_diagram in diagram_images
        assert invalid_diagram not in diagram_images


def test_generate_images_creates_output_dir(tmp_path: Path):
    """Test that generate_images creates the output directory if it doesn't exist."""
    output_dir = tmp_path / "nonexistent"
    diagrams = [MermaidDiagram("graph TD\nA-->B", 1, 2, "")]

    with patch("subprocess.run") as mock_run:
        mock_run.return_value.returncode = 0

        ImageGenerator.generate_images(diagrams, output_dir)

        assert output_dir.exists()
        assert output_dir.is_dir()
