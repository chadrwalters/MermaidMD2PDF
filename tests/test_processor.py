"""Tests for the Mermaid processor component."""

import textwrap
import pytest

from mermaidmd2pdf.processor import MermaidDiagram, MermaidProcessor

# Test constants
EXPECTED_LINE_NUMBER = 4
EXPECTED_DIAGRAM_COUNT = 2


def test_extract_diagrams_fenced():
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

    diagrams = MermaidProcessor.extract_diagrams(markdown)
    assert len(diagrams) == 1
    assert diagrams[0].content == "graph TD\nA[Start] --> B[End]"
    assert diagrams[0].start_line == EXPECTED_LINE_NUMBER
    assert "```mermaid" in diagrams[0].original_text


def test_extract_diagrams_inline():
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

    diagrams = MermaidProcessor.extract_diagrams(markdown)
    assert len(diagrams) == 1
    assert diagrams[0].content == "sequenceDiagram\nA->>B: Hello"
    assert diagrams[0].start_line == EXPECTED_LINE_NUMBER
    assert "<mermaid>" in diagrams[0].original_text


def test_extract_diagrams_multiple():
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

    diagrams = MermaidProcessor.extract_diagrams(markdown)
    assert len(diagrams) == EXPECTED_DIAGRAM_COUNT
    assert "graph TD" in diagrams[0].content
    assert "sequenceDiagram" in diagrams[1].content


def test_validate_diagram_valid():
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

    for content in valid_diagrams:
        diagram = MermaidDiagram(
            content=content, start_line=1, end_line=2, original_text=""
        )
        is_valid, error = MermaidProcessor.validate_diagram(diagram)
        assert is_valid
        assert error is None


def test_validate_diagram_invalid():
    """Test validation of invalid Mermaid diagrams."""
    invalid_diagrams = [
        "",  # Empty
        "invalid content",  # No diagram type
        "graph",  # Incomplete graph
    ]

    for content in invalid_diagrams:
        diagram = MermaidDiagram(
            content=content, start_line=1, end_line=2, original_text=""
        )
        is_valid, error = MermaidProcessor.validate_diagram(diagram)
        assert not is_valid
        assert error is not None


def test_process_markdown_valid():
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

    processed_text, errors = MermaidProcessor.process_markdown(markdown)
    assert processed_text == markdown
    assert not errors


def test_process_markdown_invalid():
    """Test processing of Markdown with invalid diagrams."""
    markdown = textwrap.dedent(
        """
        # Test Document

        ```mermaid
        invalid content
        ```
        """
    )

    processed_text, errors = MermaidProcessor.process_markdown(markdown)
    assert processed_text == markdown
    assert len(errors) == 1
    assert "Invalid diagram at line" in errors[0]
