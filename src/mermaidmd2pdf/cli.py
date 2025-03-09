"""Command-line interface for MermaidMD2PDF."""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

import click

from mermaidmd2pdf.dependencies import DependencyChecker
from mermaidmd2pdf.generator import ImageGenerator, PDFGenerator
from mermaidmd2pdf.logging import get_logger, setup_logging
from mermaidmd2pdf.processor import MermaidDiagram, MermaidProcessor
from mermaidmd2pdf.utils import temp_directory
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
        logger.info("ℹ️  No Mermaid diagrams found in the document")

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
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("output_file", type=click.Path(dir_okay=False))
@click.option(
    "--title",
    help="Optional title for the PDF document",
    type=str,
    default=None,
)
@click.option(
    "--verbose",
    help="Enable verbose logging",
    is_flag=True,
    default=False,
)
@click.option(
    "--temp-dir",
    help="Directory for temporary files (default: system temp dir)",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
    default=None,
)
@click.option(
    "--cache-size",
    help=f"Maximum number of diagrams to cache (default: {DEFAULT_CACHE_SIZE})",
    type=int,
    default=DEFAULT_CACHE_SIZE,
)
@click.option(
    "--no-cache",
    help="Disable diagram caching",
    is_flag=True,
    default=False,
)
@click.option(
    "--clean",
    help="Clean temporary files after processing",
    is_flag=True,
    default=False,
)
def main(
    input_file: str,
    output_file: str,
    title: Optional[str] = None,
    verbose: bool = False,
    temp_dir: Optional[Path] = None,
    cache_size: int = DEFAULT_CACHE_SIZE,
    no_cache: bool = False,
    clean: bool = False,
) -> None:
    """Convert a Markdown file with Mermaid diagrams to PDF.

    This tool converts Markdown files containing Mermaid diagrams to PDF documents.
    It supports various diagram types including flowcharts, sequence diagrams,
    class diagrams, and more.

    Examples:
        Basic usage:
        $ mermaidmd2pdf input.md output.pdf

        With title and verbose logging:
        $ mermaidmd2pdf --title "My Document" --verbose input.md output.pdf

        Using custom temporary directory:
        $ mermaidmd2pdf --temp-dir ./tmp input.md output.pdf

        Disable caching for large documents:
        $ mermaidmd2pdf --no-cache input.md output.pdf

    Args:
        input_file: Path to the input Markdown file
        output_file: Path to the output PDF file
        title: Optional title for the PDF document
        verbose: Enable verbose logging
        temp_dir: Directory for temporary files
        cache_size: Maximum number of diagrams to cache
        no_cache: Disable diagram caching
        clean: Clean temporary files after processing
    """
    # Set up logging
    setup_logging(verbose)

    try:
        # Validate environment and files
        validate_environment()
        validate_files(input_file, output_file)

        # Process input file
        input_path = Path(input_file)
        processed_text, diagrams = process_markdown_content(input_path)

        # Use context manager for temporary directory
        with temp_directory(
            base_dir=temp_dir if temp_dir else None,
            cleanup=clean or not temp_dir,  # Clean up if requested or using system temp
        ) as work_dir:
            # Generate images for diagrams
            diagram_images = generate_diagram_images(
                diagrams,
                input_path.parent,
                temp_dir=work_dir if no_cache else None,
                cache_size=0 if no_cache else cache_size,
            )

            # Create final PDF
            create_pdf(processed_text, diagram_images, Path(output_file), title)

            if diagram_images:
                logger.info(f"✨ Generated {len(diagram_images)} diagram images")

    except click.ClickException:
        raise
    except Exception as e:
        logger.error(f"❌ An unexpected error occurred: {e}")
        raise click.ClickException(str(e)) from e


if __name__ == "__main__":
    main()
