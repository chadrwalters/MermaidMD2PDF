"""Command-line interface for MermaidMD2PDF."""

import logging
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import click

from mermaidmd2pdf.dependencies import DependencyChecker
from mermaidmd2pdf.generator import ImageGenerator, PDFGenerator
from mermaidmd2pdf.logging import get_logger
from mermaidmd2pdf.processor import MermaidDiagram, MermaidProcessor
from mermaidmd2pdf.validator import FileValidator

logger = get_logger(__name__)

# Default configuration
DEFAULT_CACHE_SIZE = 100  # Number of diagrams to cache


def validate_environment() -> None:
    """Verify all required dependencies are installed.

    Raises:
        click.ClickException: If any dependency is missing
    """
    logger.info("🔍 Checking dependencies...")
    checker = DependencyChecker()
    is_satisfied, error = checker.verify_all()
    if not is_satisfied:
        raise click.ClickException(error or "Unknown dependency error")


def validate_files(input_file: str, output_file: str) -> None:
    """Validate input and output file paths.

    Args:
        input_file: Path to the input Markdown file
        output_file: Path to the output PDF file

    Raises:
        click.ClickException: If either file path is invalid
    """
    logger.info("🔍 Validating files...")
    validator = FileValidator()

    is_valid, error = validator.validate_input_file(input_file)
    if not is_valid:
        raise click.ClickException(error or "Invalid input file")

    is_valid, error = validator.validate_output_file(output_file)
    if not is_valid:
        raise click.ClickException(error or "Invalid output file")


def process_markdown_content(input_path: Path) -> Tuple[str, List[MermaidDiagram]]:
    """Process markdown content and extract diagrams.

    Args:
        input_path: Path to the input Markdown file

    Returns:
        Tuple containing processed text and list of extracted diagrams

    Raises:
        click.ClickException: If markdown processing fails
    """
    logger.info("📖 Reading input file...")
    try:
        with open(input_path, encoding="utf-8") as f:
            content = f.read()
    except Exception as e:
        raise click.ClickException(f"Failed to read input file: {e}") from e

    logger.info("🔄 Processing Markdown...")
    processor = MermaidProcessor()
    processed_text, errors = processor.process_markdown(content)
    if errors:
        raise click.ClickException(f"Markdown processing failed: {'; '.join(errors)}")

    diagrams = processor.extract_diagrams(content)
    if not diagrams:
        logger.info("No Mermaid diagrams found in the document")

    return processed_text, diagrams


def generate_diagram_images(
    diagrams: List[MermaidDiagram],
    input_dir: Path,
    temp_dir: Optional[Path] = None,
    cache_size: int = DEFAULT_CACHE_SIZE,
) -> Dict[MermaidDiagram, Path]:
    """Generate images for Mermaid diagrams.

    Args:
        diagrams: List of Mermaid diagram definitions
        input_dir: Directory containing the input file
        temp_dir: Optional directory for temporary files
        cache_size: Maximum number of diagrams to cache

    Returns:
        Dictionary mapping diagram definitions to image paths

    Raises:
        click.ClickException: If image generation fails
    """
    image_generator = ImageGenerator(cache_dir=temp_dir)
    diagram_images, errors = image_generator.generate_images(diagrams, input_dir)
    if errors:
        raise click.ClickException(f"Failed to generate images: {'; '.join(errors)}")
    return diagram_images


def create_pdf(
    processed_text: str,
    diagram_images: Dict[MermaidDiagram, Path],
    output_path: Path,
    title: Optional[str] = None,
) -> None:
    """Generate the final PDF document.

    Args:
        processed_text: Processed markdown text
        diagram_images: Dictionary of diagram definitions and their image paths
        output_path: Path where the PDF should be saved
        title: Optional title for the PDF document

    Raises:
        click.ClickException: If PDF generation fails
    """
    logger.info("📄 Converting to PDF...")
    success, error = PDFGenerator.generate_pdf(
        processed_text, diagram_images, output_path, title=title
    )
    if not success:
        raise click.ClickException(error or "Failed to generate PDF")

    logger.info(f"✨ Successfully generated PDF: {output_path}")


@click.command()
@click.argument("input_file", type=click.Path(exists=True))
@click.argument("output_file", type=click.Path())
@click.option(
    "--theme",
    type=click.Choice(["light", "dark"]),
    default="light",
    help="Theme for the generated PDF",
)
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug logging",
    default=False,
)
def main(
    input_file: str,
    output_file: str,
    theme: str,
    debug: bool,
) -> None:
    """Convert Markdown with Mermaid diagrams to PDF."""
    # Configure logging
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(levelname)s: %(message)s",
    )

    # Validate files
    validator = FileValidator()
    is_valid, error = validator.validate_input_file(input_file)
    if not is_valid:
        logger.error(error)
        sys.exit(1)

    is_valid, error = validator.validate_output_file(output_file)
    if not is_valid:
        logger.error(error)
        sys.exit(1)

    # Process the file
    try:
        generator = PDFGenerator()
        generator.convert(input_file, output_file)
        logger.info(f"Successfully converted {input_file} to {output_file}")
    except Exception as e:
        logger.error(f"Error converting file: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
