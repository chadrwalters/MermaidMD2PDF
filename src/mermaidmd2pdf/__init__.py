"""MermaidMD2PDF - Convert Markdown files with Mermaid diagrams to PDF."""

from mermaidmd2pdf.cli import main
from mermaidmd2pdf.generator import convert_to_pdf
from mermaidmd2pdf.processor import process_markdown
from mermaidmd2pdf.validator import validate_input

__version__ = "0.1.0"

__all__ = ["convert_to_pdf", "main", "process_markdown", "validate_input"]
