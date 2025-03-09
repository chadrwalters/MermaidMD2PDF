#!/usr/bin/env python3
"""Performance profiling script for MermaidMD2PDF."""

import cProfile
import pstats
from pathlib import Path

from mermaidmd2pdf.generator import ImageGenerator, PDFGenerator
from mermaidmd2pdf.processor import MermaidProcessor


def profile_markdown_processing(input_file: Path) -> None:
    """Profile markdown processing performance."""
    processor = MermaidProcessor()
    with open(input_file, encoding="utf-8") as f:
        content = f.read()

    def _process() -> None:
        processor.process_markdown(content)
        processor.extract_diagrams(content)

    profiler = cProfile.Profile()
    profiler.runctx("_process()", globals(), locals())
    stats = pstats.Stats(profiler)
    stats.sort_stats(pstats.SortKey.TIME)
    print("\nMarkdown Processing Performance:")
    stats.print_stats(20)  # Show top 20 time-consuming operations


def profile_image_generation(diagrams: list, output_dir: Path) -> None:
    """Profile image generation performance."""
    generator = ImageGenerator()

    def _generate() -> None:
        generator.generate_images(diagrams, output_dir)

    profiler = cProfile.Profile()
    profiler.runctx("_generate()", globals(), locals())
    stats = pstats.Stats(profiler)
    stats.sort_stats(pstats.SortKey.TIME)
    print("\nImage Generation Performance:")
    stats.print_stats(20)


def profile_pdf_generation(
    content: str, diagram_images: dict, output_file: Path, title: str | None = None
) -> None:
    """Profile PDF generation performance."""

    def _generate() -> None:
        PDFGenerator.generate_pdf(content, diagram_images, output_file, title=title)

    profiler = cProfile.Profile()
    profiler.runctx("_generate()", globals(), locals())
    stats = pstats.Stats(profiler)
    stats.sort_stats(pstats.SortKey.TIME)
    print("\nPDF Generation Performance:")
    stats.print_stats(20)


def main() -> None:
    """Run performance profiling on all major operations."""
    # Use a sample markdown file with diagrams
    input_file = Path("tests/data/sample.md")
    output_dir = Path("tests/data/output")
    output_dir.mkdir(exist_ok=True)

    # Profile markdown processing
    profile_markdown_processing(input_file)

    # Get diagrams for subsequent profiling
    processor = MermaidProcessor()
    with open(input_file, encoding="utf-8") as f:
        content = f.read()
    processed_text, _ = processor.process_markdown(content)
    diagrams = processor.extract_diagrams(content)

    # Profile image generation
    profile_image_generation(diagrams, output_dir)

    # Generate images for PDF profiling
    generator = ImageGenerator()
    diagram_images, _ = generator.generate_images(diagrams, output_dir)

    # Profile PDF generation
    output_file = output_dir / "output.pdf"
    profile_pdf_generation(processed_text, diagram_images, output_file)


if __name__ == "__main__":
    main()
