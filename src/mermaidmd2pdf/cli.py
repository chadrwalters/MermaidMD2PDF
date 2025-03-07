"""Command-line interface for MermaidMD2PDF."""

from pathlib import Path
from typing import Optional

import click

from mermaidmd2pdf.dependencies import DependencyChecker
from mermaidmd2pdf.generator import ImageGenerator
from mermaidmd2pdf.pdf import PDFGenerator
from mermaidmd2pdf.processor import MermaidProcessor
from mermaidmd2pdf.validator import FileValidator


@click.command()
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("output_file", type=click.Path(dir_okay=False))
@click.option(
    "--title",
    help="Optional title for the PDF document",
    type=str,
    default=None,
)
def main(input_file: str, output_file: str, title: Optional[str] = None) -> None:
    """Convert a Markdown file with Mermaid diagrams to PDF.

    Args:
        input_file: Path to the input Markdown file
        output_file: Path to the output PDF file
        title: Optional title for the PDF document
    """
    # Check dependencies
    checker = DependencyChecker()
    is_satisfied, error = checker.verify_all()
    if not is_satisfied:
        raise click.ClickException(error or "Unknown dependency error")

    # Validate input and output files
    validator = FileValidator()
    is_valid, error = validator.validate_input_file(str(input_file))
    if not is_valid:
        raise click.ClickException(error or "Invalid input file")

    is_valid, error = validator.validate_output_file(str(output_file))
    if not is_valid:
        raise click.ClickException(error or "Invalid output file")

    # Read and process input file
    input_path = Path(input_file)
    with open(input_path, encoding="utf-8") as f:
        content = f.read()

    # Process markdown and extract diagrams
    processor = MermaidProcessor()
    processed_text, errors = processor.process_markdown(content)
    if errors:
        raise click.ClickException(f"Markdown processing failed: {'; '.join(errors)}")

    diagrams = processor.extract_diagrams(content)

    # Create temporary directory for images
    image_generator = ImageGenerator()
    diagram_images, errors = image_generator.generate_images(
        diagrams, input_path.parent
    )
    if errors:
        raise click.ClickException(f"Failed to generate images: {'; '.join(errors)}")

    # Generate PDF
    output_path = Path(output_file)
    pdf_generator = PDFGenerator()
    success, error = pdf_generator.generate_pdf(
        processed_text, diagram_images, output_path, title=title
    )
    if not success:
        raise click.ClickException(error or "Failed to generate PDF")


if __name__ == "__main__":
    main()
