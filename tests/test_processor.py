"""Tests for the Markdown and Mermaid diagram processor."""

import textwrap
from pathlib import Path

from mermaidmd2pdf.processor import MermaidDiagram, MermaidProcessor

# Test constants
EXPECTED_LINE_NUMBER = 4
EXPECTED_SINGLE_DIAGRAM_COUNT = 1  # Test cases with a single diagram
EXPECTED_MULTIPLE_DIAGRAM_COUNT = 2  # Test cases with multiple diagrams
EXPECTED_ERROR_COUNT = 0  # No errors expected for valid diagrams
EXPECTED_INVALID_ERROR_COUNT = 1  # One error expected for invalid diagrams


def test_extract_diagrams_fenced() -> None:
    """Test extraction of fenced Mermaid diagrams."""
    markdown = textwrap.dedent(
        """
        # Test Document

        ```mermaid
        graph TD
        A[Start] --> B[End]
        ```

        Some text here.
        """
    )

    processor = MermaidProcessor()
    diagrams = processor.extract_diagrams(markdown)
    assert len(diagrams) == EXPECTED_SINGLE_DIAGRAM_COUNT
    assert diagrams[0].content == "graph TD\nA[Start] --> B[End]"
    assert diagrams[0].start_line == EXPECTED_LINE_NUMBER
    assert "```mermaid" in diagrams[0].original_text


def test_extract_diagrams_inline() -> None:
    """Test extraction of inline Mermaid diagrams."""
    markdown = textwrap.dedent(
        """
        # Test Document

        <mermaid>
        sequenceDiagram
        A->>B: Hello
        </mermaid>

        Some text here.
        """
    )

    processor = MermaidProcessor()
    diagrams = processor.extract_diagrams(markdown)
    assert len(diagrams) == EXPECTED_SINGLE_DIAGRAM_COUNT
    assert diagrams[0].content == "sequenceDiagram\nA->>B: Hello"
    assert diagrams[0].start_line == EXPECTED_LINE_NUMBER
    assert "<mermaid>" in diagrams[0].original_text


def test_extract_diagrams_multiple() -> None:
    """Test extraction of multiple Mermaid diagrams."""
    markdown = textwrap.dedent(
        """
        # Test Document

        ```mermaid
        graph TD
        A[Start] --> B[End]
        ```

        Some text here.

        <mermaid>
        sequenceDiagram
        A->>B: Hello
        </mermaid>
        """
    )

    processor = MermaidProcessor()
    diagrams = processor.extract_diagrams(markdown)
    assert len(diagrams) == EXPECTED_MULTIPLE_DIAGRAM_COUNT
    assert "graph TD" in diagrams[0].content
    assert "sequenceDiagram" in diagrams[1].content


def test_validate_diagram_valid() -> None:
    """Test validation of valid Mermaid diagrams."""
    valid_diagrams = [
        "graph TD\nA[Start] --> B[End]",
        "sequenceDiagram\nA->>B: Hello",
        "classDiagram\nClass01 <|-- Class02",
        "stateDiagram\ns1 --> s2",
        "erDiagram\nCUSTOMER ||--o{ ORDER",
        'pie\ntitle Pie Chart\n"Dogs" : 386',
        "gantt\ntitle Timeline\nsection Section\nTask1: 2024-01-01, 7d",
        "flowchart LR\nA-->B",
    ]

    processor = MermaidProcessor()
    for content in valid_diagrams:
        diagram = MermaidDiagram(
            content=content, start_line=1, end_line=2, original_text=""
        )
        is_valid, error = processor.validate_diagram(diagram)
        assert is_valid, f"Diagram should be valid: {error}"


def test_validate_diagram_invalid() -> None:
    """Test validation of invalid Mermaid diagrams."""
    invalid_diagrams = [
        "",  # Empty
        "invalid content",  # No diagram type
        "graph",  # Incomplete graph
    ]

    processor = MermaidProcessor()
    for content in invalid_diagrams:
        diagram = MermaidDiagram(
            content=content, start_line=1, end_line=2, original_text=""
        )
        is_valid, error = processor.validate_diagram(diagram)
        assert not is_valid, "Diagram should be invalid"


def test_process_markdown_valid() -> None:
    """Test processing of Markdown with valid diagrams."""
    markdown = textwrap.dedent(
        """
        # Test Document

        ```mermaid
        graph TD
        A[Start] --> B[End]
        ```
        """
    )

    processor = MermaidProcessor()
    processed_text, errors = processor.process_markdown(markdown)
    assert not errors
    assert processed_text == markdown


def test_process_markdown_invalid() -> None:
    """Test processing of Markdown with invalid diagrams."""
    markdown = textwrap.dedent(
        """
        # Test Document

        ```mermaid
        invalid content
        ```
        """
    )

    processor = MermaidProcessor()
    processed_text, errors = processor.process_markdown(markdown)
    assert errors
    assert processed_text == markdown


def test_process_markdown_success(temp_dir: Path) -> None:
    """Test processing of Markdown with valid diagrams."""
    markdown = textwrap.dedent(
        """
        # Test Document

        ```mermaid
        graph TD
        A[Start] --> B[End]
        ```
        """
    )

    processor = MermaidProcessor()
    processed_text, errors = processor.process_markdown(markdown)
    assert not errors
    assert processed_text == markdown
