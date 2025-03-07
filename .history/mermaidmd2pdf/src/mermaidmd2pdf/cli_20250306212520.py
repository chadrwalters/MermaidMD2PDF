"""Command-line interface for MermaidMD2PDF."""
import sys

import click

from mermaidmd2pdf.validator import FileValidator


@click.command()
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("output_file", type=click.Path(dir_okay=False))
def main(input_file: str, output_file: str) -> None:
    """Convert Markdown files with Mermaid diagrams to PDF.

    Args:
        input_file: Path to input Markdown file
        output_file: Path to output PDF file
    """
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

    click.echo(f"Converting {input_file} to {output_file}")
    # TODO: Implement actual conversion logic in future phases
