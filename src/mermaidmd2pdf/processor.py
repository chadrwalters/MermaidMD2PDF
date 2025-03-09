"""Markdown and Mermaid diagram processing component."""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from mermaidmd2pdf.logging import get_logger

logger = get_logger(__name__)

# Constants
MIN_WORDS_FOR_DIRECTION = 2


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

        self.diagram_pattern = re.compile(
            r"```mermaid\n(.*?)\n```",
            re.DOTALL,
        )

    def validate_diagram(self, diagram: str) -> Tuple[bool, Optional[str]]:
        """Validate a Mermaid diagram definition.

        Args:
            diagram: Diagram definition

        Returns:
            Tuple of (is_valid, error_message)
        """
        lines = diagram.strip().split("\n")
        if not lines:
            return False, "Empty diagram"

        first_line = lines[0].strip()
        if not first_line:
            return False, "Empty first line"

        first_word = first_line.split()[0].lower()

        # Handle graph/flowchart with direction
        if first_word in ["graph", "flowchart"]:
            if len(first_line.split()) < MIN_WORDS_FOR_DIRECTION:
                msg = (
                    f"Missing direction for {first_word} diagram at lines {len(lines)}"
                )
                return False, msg

        return True, None

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
                    f"Invalid Mermaid diagram at lines {len(diagram.split('\n'))}"
                )
                errors.append(error or error_msg)

        return content, errors

    def extract_diagrams(self, content: str) -> List[str]:
        """Extract Mermaid diagrams from Markdown content.

        Args:
            content: Markdown content

        Returns:
            List of diagram definitions
        """
        return self.diagram_pattern.findall(content)
