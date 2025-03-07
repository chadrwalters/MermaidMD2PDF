"""Command-line interface for MermaidMD2PDF."""
import click


@click.command()
@click.argument("input_file", type=click.Path(exists=True, dir_okay=False))
@click.argument("output_file", type=click.Path(dir_okay=False))
def main(input_file: str, output_file: str) -> None:
    """Convert Markdown files with Mermaid diagrams to PDF.

    Args:
        input_file: Path to input Markdown file
        output_file: Path to output PDF file
    """
    click.echo(f"Converting {input_file} to {output_file}")
    # Placeholder for actual conversion logic
