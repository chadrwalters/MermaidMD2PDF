"""Mermaid diagram processor component for MermaidMD2PDF."""

import re
from dataclasses import dataclass
from typing import ClassVar, List, Optional, Set, Tuple


@dataclass(frozen=True)
class MermaidDiagram:
    """Represents a Mermaid diagram found in Markdown text."""

    content: str
    start_line: int
    end_line: int
    original_text: str

    def __hash__(self) -> int:
        """Return a hash value for the diagram."""
        return hash((self.content, self.start_line, self.end_line, self.original_text))

    def __eq__(self, other: object) -> bool:
        """Compare two diagrams for equality."""
        if not isinstance(other, MermaidDiagram):
            return NotImplemented
        return (
            self.content == other.content
            and self.start_line == other.start_line
            and self.end_line == other.end_line
            and self.original_text == other.original_text
        )


class MermaidProcessor:
    """Process Markdown files to extract and validate Mermaid diagrams."""

    MERMAID_FENCE_PATTERN = re.compile(r"```mermaid\n(.*?)\n```", re.DOTALL)
    MERMAID_INLINE_PATTERN = re.compile(r"<mermaid>(.*?)</mermaid>", re.DOTALL)
    MIN_DIAGRAM_LINES = 2  # Type + at least one element
    VALID_DIAGRAM_TYPES: ClassVar[Set[str]] = {
        "graph",
        "sequencediagram",
        "classdiagram",
        "statediagram",
        "erdiagram",
        "flowchart",
        "gantt",
        "pie",
        "journey",
    }

    @staticmethod
    def extract_diagrams(markdown_text: str) -> List[MermaidDiagram]:
        """Extract Mermaid diagrams from Markdown text.

        Args:
            markdown_text: The Markdown text to process

        Returns:
            List of MermaidDiagram objects containing the extracted diagrams
        """
        diagrams = []

        # Find fenced Mermaid blocks
        for match in MermaidProcessor.MERMAID_FENCE_PATTERN.finditer(markdown_text):
            start_pos = markdown_text.count("\n", 0, match.start()) + 1
            end_pos = markdown_text.count("\n", 0, match.end()) + 1
            diagrams.append(
                MermaidDiagram(
                    content=match.group(1).strip(),
                    start_line=start_pos,
                    end_line=end_pos,
                    original_text=match.group(0),
                )
            )

        # Find inline Mermaid blocks
        for match in MermaidProcessor.MERMAID_INLINE_PATTERN.finditer(markdown_text):
            start_pos = markdown_text.count("\n", 0, match.start()) + 1
            end_pos = markdown_text.count("\n", 0, match.end()) + 1
            diagrams.append(
                MermaidDiagram(
                    content=match.group(1).strip(),
                    start_line=start_pos,
                    end_line=end_pos,
                    original_text=match.group(0),
                )
            )

        return diagrams

    @staticmethod
    def validate_diagram(diagram: MermaidDiagram) -> Tuple[bool, Optional[str]]:
        """Validate a Mermaid diagram for syntax errors.

        Args:
            diagram: The MermaidDiagram to validate

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if valid, False otherwise
            - error_message: None if valid, error description if invalid
        """
        content = diagram.content.strip()

        # Check for empty content
        if not content:
            return False, "Empty diagram content"

        # Check for minimum content length (type + at least one element)
        if len(content.split("\n")) < MermaidProcessor.MIN_DIAGRAM_LINES:
            return False, "Diagram must contain at least one element"

        # Basic syntax validation
        content.split("\n")[0].strip().lower()
        if not any(
            diagram_type.lower() in content.lower()
            for diagram_type in MermaidProcessor.VALID_DIAGRAM_TYPES
        ):
            return False, (
                f"Invalid diagram type at line {diagram.start_line}. "
                f"Must be one of: {', '.join(MermaidProcessor.VALID_DIAGRAM_TYPES)}"
            )

        return True, None

    @staticmethod
    def process_markdown(markdown_text: str) -> Tuple[str, List[str]]:
        """Process Markdown text, validating all Mermaid diagrams.

        Args:
            markdown_text: The Markdown text to process

        Returns:
            Tuple of (processed_text, errors)
            - processed_text: The original text if all diagrams are valid
            - errors: List of error messages, empty if all diagrams are valid
        """
        errors = []
        diagrams = MermaidProcessor.extract_diagrams(markdown_text)

        for diagram in diagrams:
            is_valid, error = MermaidProcessor.validate_diagram(diagram)
            if not is_valid:
                errors.append(f"Invalid diagram at line {diagram.start_line}: {error}")

        return markdown_text, errors
