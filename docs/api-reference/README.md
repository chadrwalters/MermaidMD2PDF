# MermaidMD2PDF API Reference

This document provides detailed API documentation for the MermaidMD2PDF library.

## Table of Contents

1. [Overview](#overview)
2. [Core Components](#core-components)
3. [CLI Interface](#cli-interface)
4. [Python API](#python-api)
5. [Error Handling](#error-handling)
6. [Configuration](#configuration)

## Overview

MermaidMD2PDF provides both a command-line interface and a Python API for converting Markdown documents with Mermaid diagrams to PDF.

## Core Components

### File Validator

```python
class FileValidator:
    """Validates input and output files for the conversion process."""

    def validate_input_file(self, file_path: Path) -> None:
        """
        Validate the input Markdown file.

        Args:
            file_path: Path to the input file

        Raises:
            FileNotFoundError: If the file doesn't exist
            PermissionError: If the file can't be read
            ValueError: If the file extension is invalid
        """
        pass

    def validate_output_file(self, file_path: Path) -> None:
        """
        Validate the output PDF file path.

        Args:
            file_path: Path to the output file

        Raises:
            PermissionError: If the directory can't be written to
            ValueError: If the file extension is invalid
        """
        pass
```

### Dependency Checker

```python
class DependencyChecker:
    """Checks for required system and Python package dependencies."""

    def check_system_dependencies(self) -> None:
        """
        Check for required system dependencies (Pandoc, Mermaid CLI).

        Raises:
            DependencyError: If any required system dependency is missing
        """
        pass

    def check_python_dependencies(self) -> None:
        """
        Check for required Python package dependencies.

        Raises:
            DependencyError: If any required Python package is missing
        """
        pass
```

### Mermaid Processor

```python
class MermaidProcessor:
    """Processes and validates Mermaid diagrams in Markdown."""

    def extract_diagrams(self, content: str) -> List[MermaidDiagram]:
        """
        Extract Mermaid diagrams from Markdown content.

        Args:
            content: Markdown content to process

        Returns:
            List of extracted Mermaid diagrams

        Raises:
            SyntaxError: If a diagram has invalid syntax
        """
        pass

    def validate_diagram(self, diagram: MermaidDiagram) -> None:
        """
        Validate a Mermaid diagram's syntax.

        Args:
            diagram: Diagram to validate

        Raises:
            SyntaxError: If the diagram has invalid syntax
        """
        pass
```

### Image Generator

```python
class ImageGenerator:
    """Generates images from Mermaid diagrams."""

    def generate_image(self, diagram: MermaidDiagram, output_path: Path) -> None:
        """
        Generate an image from a Mermaid diagram.

        Args:
            diagram: Diagram to convert
            output_path: Path to save the generated image

        Raises:
            ImageGenerationError: If image generation fails
        """
        pass
```

### PDF Generator

```python
class PDFGenerator:
    """Generates PDFs from Markdown with embedded diagrams."""

    def generate_pdf(
        self,
        markdown_path: Path,
        output_path: Path,
        title: Optional[str] = None
    ) -> None:
        """
        Generate a PDF from a Markdown file with embedded diagrams.

        Args:
            markdown_path: Path to the input Markdown file
            output_path: Path to save the generated PDF
            title: Optional title for the PDF

        Raises:
            PDFGenerationError: If PDF generation fails
        """
        pass
```

## CLI Interface

The command-line interface provides a simple way to use MermaidMD2PDF:

```bash
mermaidmd2pdf [OPTIONS] INPUT_FILE OUTPUT_FILE
```

### Options

- `--title TEXT`: Set the PDF title
- `--help`: Show help message and exit
- `--version`: Show version and exit

### Examples

Basic usage:
```bash
mermaidmd2pdf input.md output.pdf
```

With title:
```bash
mermaidmd2pdf --title "My Document" input.md output.pdf
```

## Python API

### Main Interface

```python
from mermaidmd2pdf import convert_markdown_to_pdf

# Convert a Markdown file to PDF
convert_markdown_to_pdf(
    input_file: Path,
    output_file: Path,
    title: Optional[str] = None
) -> None
```

### Example Usage

```python
from pathlib import Path
from mermaidmd2pdf import convert_markdown_to_pdf

# Convert a document
convert_markdown_to_pdf(
    input_file=Path("input.md"),
    output_file=Path("output.pdf"),
    title="My Document"
)
```

## Error Handling

The library defines several custom exceptions:

```python
class MermaidMD2PDFError(Exception):
    """Base exception for all MermaidMD2PDF errors."""
    pass

class DependencyError(MermaidMD2PDFError):
    """Raised when required dependencies are missing."""
    pass

class FileValidationError(MermaidMD2PDFError):
    """Raised when file validation fails."""
    pass

class DiagramError(MermaidMD2PDFError):
    """Raised when diagram processing fails."""
    pass

class PDFGenerationError(MermaidMD2PDFError):
    """Raised when PDF generation fails."""
    pass
```

## Configuration

The library can be configured through environment variables:

- `MERMAIDMD2PDF_TEMP_DIR`: Directory for temporary files
- `MERMAIDMD2PDF_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

Example:
```bash
export MERMAIDMD2PDF_TEMP_DIR="/tmp/mermaidmd2pdf"
export MERMAIDMD2PDF_LOG_LEVEL="DEBUG"
```
