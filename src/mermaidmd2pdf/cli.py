"""Command-line interface for MermaidMD2PDF."""

import sys
import tempfile
from pathlib import Path

import click

from mermaidmd2pdf.dependencies import DependencyChecker
from mermaidmd2pdf.generator import ImageGenerator
from mermaidmd2pdf.pdf import PDFGenerator
from mermaidmd2pdf.processor import MermaidProcessor
from mermaidmd2pdf.validator import FileValidator


@click.command()
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("output_file", type=click.Path(dir_okay=False))
@click.option("--title", help="Optional document title")
def main(input_file: str, output_file: str, title: str | None = None) -> None:
    """Convert Markdown files with Mermaid diagrams to PDF.

    Args:
        input_file: Path to input Markdown file
        output_file: Path to output PDF file
        title: Optional document title
    """
    # Check dependencies
    is_satisfied, error = DependencyChecker.verify_all()
    if not is_satisfied:
        click.echo(f"Error: {error}", err=True)
        sys.exit(1)

    # Validate input file
    is_valid, error = FileValidator.validate_input_file(input_file)
    if not is_valid:
        click.echo(f"Error: {error}", err=True)
        sys.exit(1)

    # Validate output file
    is_valid, error = FileValidator.validate_output_file(output_file)
    if not is_valid:
        click.echo(f"Error: {error}", err=True)
        sys.exit(1)

    # Read input file
    try:
        markdown_text = Path(input_file).read_text()
    except Exception as e:
        click.echo(f"Error reading input file: {e!s}", err=True)
        sys.exit(1)

    # Process Markdown and extract diagrams
    markdown_text, errors = MermaidProcessor.process_markdown(markdown_text)
    if errors:
        click.echo("Found invalid Mermaid diagrams:", err=True)
        for error in errors:
            click.echo(f"  - {error}", err=True)
        sys.exit(1)

    # Create temporary directory for diagram images
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Extract and validate diagrams
        diagrams = MermaidProcessor.extract_diagrams(markdown_text)
        if not diagrams:
            click.echo("No Mermaid diagrams found in input file")

        # Generate images for diagrams
        diagram_images, errors = ImageGenerator.generate_images(diagrams, temp_path)
        if errors:
            click.echo("Failed to generate some diagram images:", err=True)
            for error in errors:
                click.echo(f"  - {error}", err=True)
            sys.exit(1)

        # Generate PDF
        success, error = PDFGenerator.generate_pdf(
            markdown_text, diagram_images, Path(output_file), title
        )
        if not success:
            click.echo(f"Error generating PDF: {error}", err=True)
            sys.exit(1)

    click.echo(f"Successfully converted {input_file} to {output_file}")


if __name__ == "__main__":
    main()
