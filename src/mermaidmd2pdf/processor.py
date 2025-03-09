"""Markdown and Mermaid diagram processing component."""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from mermaidmd2pdf.logging import get_logger

logger = get_logger(__name__)


@dataclass(frozen=True)  # Make the dataclass immutable
class MermaidDiagram:
    """Represents a Mermaid diagram extracted from Markdown.

    This class is immutable (frozen=True) to ensure thread safety when processing
    multiple diagrams concurrently and to make it suitable as a dictionary key.
    """

    content: str  # The actual Mermaid diagram content without fences
    start_line: int  # 1-based line number where the diagram starts in source
    end_line: int  # 1-based line number where the diagram ends in source
    original_text: str  # Complete original text including fences/tags
    config: Optional[Dict[str, Any]] = None

    def __hash__(self) -> int:
        """Make MermaidDiagram hashable based on its content and position.

        The hash is based on both content and config to ensure diagrams with
        different configurations are treated as distinct, even if content is same.
        This is important for caching and diagram-to-image mapping.
        """
        config_str = str(sorted(self.config.items())) if self.config else ""
        return hash((self.content, self.start_line, self.end_line, config_str))

    def __eq__(self, other: object) -> bool:
        """Compare MermaidDiagram instances for equality.

        Two diagrams are considered equal if they have the same content,
        position, and configuration. This is used for deduplication and
        cache lookups.
        """
        if not isinstance(other, MermaidDiagram):
            return NotImplemented
        return (
            self.content == other.content
            and self.start_line == other.start_line
            and self.end_line == other.end_line
            and self.config == other.config
        )


class MermaidProcessor:
    """Processes Markdown text and extracts Mermaid diagrams."""

    def __init__(self) -> None:
        # Define valid diagram types with their case-sensitive names
        self.DIAGRAM_TYPES: Dict[str, Dict[str, Any]] = {
            "sequencediagram": {"name": "sequenceDiagram", "min_lines": 2},
            "classdiagram": {"name": "classDiagram", "min_lines": 2},
            "flowchart": {"name": "flowchart", "min_lines": 2},
            "graph": {"name": "graph", "min_lines": 2},
            "pie": {"name": "pie", "min_lines": 2},
            "erdiagram": {"name": "erDiagram", "min_lines": 2},
            "statediagram": {"name": "stateDiagram", "min_lines": 2},
            "gantt": {"name": "gantt", "min_lines": 2},
        }

    def validate_diagram(self, diagram: MermaidDiagram) -> Tuple[bool, Optional[str]]:
        """Validate a Mermaid diagram.

        This method performs several validation checks:
        1. Verifies the diagram has non-empty content
        2. Checks if it starts with a valid diagram type
        3. For graph/flowchart types, ensures direction is specified
        4. Verifies minimal content requirements are met

        Args:
            diagram: The MermaidDiagram to validate

        Returns:
            Tuple of (is_valid, error_message)
            - is_valid: True if diagram passes all validation checks
            - error_message: None if valid, description of the error if invalid
        """
        # Basic validation: check if the diagram has content
        content_lines = diagram.content.strip().split("\n")
        if not content_lines or not content_lines[0].strip():
            msg = f"Empty diagram at lines {diagram.start_line}-{diagram.end_line}"
            logger.warning(msg)
            return False, "Empty diagram"

        # Extract the first word and normalize it
        first_line = content_lines[0].strip()
        first_word = first_line.split()[0].lower()

        # Handle graph/flowchart with direction
        if first_word in ["graph", "flowchart"]:
            if len(first_line.split()) < 2:
                msg = (
                    f"Missing direction for {first_word} diagram at lines "
                    f"{diagram.start_line}-{diagram.end_line}"
                )
                logger.warning(msg)
                return False, f"Missing direction for {first_word} diagram"
            return True, None

        # Remove any trailing colon for diagram types like sequenceDiagram:
        first_word = first_word.rstrip(":")

        # Check if it's a known diagram type
        if first_word in self.DIAGRAM_TYPES:
            return True, None

        msg = (
            "Invalid diagram type at lines "
            f"{diagram.start_line}-{diagram.end_line}: {first_word}"
        )
        logger.warning(msg)
        return False, f"Invalid diagram type: {first_word}"

    def process_markdown(self, content: str) -> Tuple[str, List[str]]:
        """Process Markdown text and validate Mermaid diagrams.

        This method serves as the main entry point for processing Markdown content.
        It extracts all Mermaid diagrams and validates each one, collecting any
        errors that occur during validation.

        Args:
            content: The Markdown text to process

        Returns:
            Tuple of (processed_text, errors)
            - processed_text: The processed Markdown text
            - errors: List of error messages, empty if no errors
        """
        errors = []
        diagrams = self.extract_diagrams(content)

        if not diagrams:
            logger.debug("No Mermaid diagrams found in content")
            return content, []

        logger.debug(f"Found {len(diagrams)} Mermaid diagrams")
        for diagram in diagrams:
            is_valid, error = self.validate_diagram(diagram)
            if not is_valid:
                error_msg = (
                    "Invalid Mermaid diagram at lines "
                    f"{diagram.start_line}-{diagram.end_line}"
                )
                errors.append(error or error_msg)

        return content, errors

    def extract_diagrams(self, content: str) -> List[MermaidDiagram]:
        """Extract Mermaid diagrams from Markdown text.

        This method uses regex patterns to find both fenced code blocks and inline
        diagrams. For each match, it calculates the exact line numbers in the source
        text for error reporting and diagram replacement.

        Args:
            content: The Markdown text to process

        Returns:
            List of MermaidDiagram objects, each containing the diagram content
            and its location in the source text
        """
        diagrams = []
        # Match both fenced code blocks and inline diagrams
        patterns = [
            (r"```mermaid\n(.*?)\n```", True),  # Fenced code blocks with newlines
            (r"<mermaid>(.*?)</mermaid>", False),  # Inline diagrams without newlines
        ]

        for pattern, _is_fenced in patterns:
            # Use re.DOTALL to make '.' match newlines, crucial for multi-line diagrams
            for match in re.finditer(pattern, content, re.DOTALL):
                # Calculate 1-based line numbers by counting newlines
                start_line = content.count("\n", 0, match.start()) + 1
                end_line = content.count("\n", 0, match.end()) + 1

                diagram = MermaidDiagram(
                    content=match.group(
                        1
                    ).strip(),  # Remove leading/trailing whitespace
                    start_line=start_line,
                    end_line=end_line,
                    original_text=match.group(0),  # Keep original text for replacement
                )
                diagrams.append(diagram)
                logger.debug(f"Extracted diagram at lines {start_line}-{end_line}")

        return diagrams
