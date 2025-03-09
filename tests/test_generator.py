"""Tests for the image generator component."""

import io
import logging
from collections.abc import Generator
from pathlib import Path

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
def multiple_diagrams() -> list[MermaidDiagram]:
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


@pytest.fixture
def log_output() -> Generator[io.StringIO, None, None]:
    """Fixture to capture log output."""
    log_stream = io.StringIO()
    handler = logging.StreamHandler(log_stream)
    handler.setFormatter(logging.Formatter("%(message)s"))
    logger = logging.getLogger("mermaidmd2pdf")
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    yield log_stream
    logger.removeHandler(handler)


def test_create_mermaid_config() -> None:
    """Test creation of Mermaid configuration."""
    generator = ImageGenerator()
    config = generator._create_mermaid_config()
    assert isinstance(config, dict)
    assert "theme" in config
    assert "themeVariables" in config


def test_generate_image_success(
    temp_output_dir: Path, sample_diagram: MermaidDiagram
) -> None:
    """Test successful image generation."""
    generator = ImageGenerator()
    success, error, image_path = generator.generate_image(
        sample_diagram, temp_output_dir
    )
    assert success
    assert error is None
    assert image_path is not None
    assert image_path.exists()
    assert image_path.stat().st_size > 0


def test_generate_image_failure(temp_output_dir: Path) -> None:
    """Test image generation failure."""
    invalid_diagram = MermaidDiagram(
        content="invalid diagram",
        start_line=1,
        end_line=2,
        original_text="```mermaid\ninvalid diagram\n```",
    )
    generator = ImageGenerator()
    success, error, image_path = generator.generate_image(
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
        generator = ImageGenerator()
        success, error, image_path = generator.generate_image(diagram, temp_output_dir)
        assert not success
        assert error is not None
        assert image_path is None


def test_generate_images_success(
    temp_output_dir: Path,
    multiple_diagrams: list[MermaidDiagram],
    log_output: io.StringIO,
) -> None:
    """Test successful generation of multiple images."""
    generator = ImageGenerator()
    diagram_images, errors = generator.generate_images(
        multiple_diagrams, temp_output_dir
    )
    output = log_output.getvalue()

    assert len(diagram_images) == len(multiple_diagrams)
    assert not errors
    assert "🔄 Processing 2 Mermaid diagrams..." in output


def test_generate_images_partial_failure(
    temp_output_dir: Path,
    multiple_diagrams: list[MermaidDiagram],
    log_output: io.StringIO,
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

    generator = ImageGenerator()
    diagram_images, errors = generator.generate_images(diagrams, temp_output_dir)
    output = log_output.getvalue()

    assert len(diagram_images) == len(multiple_diagrams)
    assert len(errors) == 1
    assert "🔄 Processing 3 Mermaid diagrams..." in output


def test_generate_images_empty_list(
    temp_output_dir: Path, log_output: io.StringIO
) -> None:
    """Test handling of empty diagram list."""
    generator = ImageGenerator()
    diagram_images, errors = generator.generate_images([], temp_output_dir)
    output = log_output.getvalue()

    assert not diagram_images
    assert not errors
    assert output == ""


def test_generate_images_with_warnings(
    temp_output_dir: Path, sample_diagram: MermaidDiagram, log_output: io.StringIO
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

    generator = ImageGenerator()
    diagram_images, errors = generator.generate_images([diagram], temp_output_dir)
    output = log_output.getvalue()

    assert len(diagram_images) == 1
    assert not errors
    assert "🔄 Processing 1 Mermaid diagram..." in output


def test_generate_images_cleanup(temp_output_dir: Path) -> None:
    """Test cleanup after image generation."""
    diagram = MermaidDiagram(
        content="graph TD\nA-->B",
        start_line=1,
        end_line=2,
        original_text="```mermaid\ngraph TD\nA-->B\n```",
    )

    generator = ImageGenerator()
    success, error, image_path = generator.generate_image(diagram, temp_output_dir)
    assert success
    assert error is None
    assert image_path is not None
    assert image_path.exists()

    # Check that temporary files are cleaned up
    temp_files = list(temp_output_dir.glob("*.mmd"))
    assert not temp_files
