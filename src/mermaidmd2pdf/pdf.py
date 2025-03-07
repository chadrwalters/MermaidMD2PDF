"""PDF generator component for MermaidMD2PDF."""

import subprocess
import tempfile
from pathlib import Path
from typing import Dict, Optional, Tuple

from mermaidmd2pdf.processor import MermaidDiagram


class PDFGenerator:
    """Generates PDF documents from Markdown with embedded images."""

    @staticmethod
    def _replace_diagrams_with_images(
        markdown_text: str, diagram_images: Dict[MermaidDiagram, Path]
    ) -> str:
        """Replace Mermaid diagrams with image references.

        Args:
            markdown_text: Original Markdown text
            diagram_images: Dictionary mapping diagrams to their image paths

        Returns:
            Modified Markdown text with diagrams replaced by image references
        """
        result = markdown_text

        # Sort diagrams by start position in reverse order to avoid position shifts
        sorted_diagrams = sorted(
            diagram_images.keys(), key=lambda d: d.start_line, reverse=True
        )

        for diagram in sorted_diagrams:
            image_path = diagram_images[diagram]
            image_ref = f"![Diagram]({image_path})"
            result = result.replace(diagram.original_text, image_ref)

        return result

    @staticmethod
    def generate_pdf(
        markdown_text: str,
        diagram_images: Dict[MermaidDiagram, Path],
        output_file: Path,
        title: Optional[str] = None,
    ) -> Tuple[bool, Optional[str]]:
        """Generate a PDF from Markdown text with embedded diagrams.

        Args:
            markdown_text: The Markdown text to convert
            diagram_images: Dictionary mapping diagrams to their image paths
            output_file: Path where the PDF should be saved
            title: Optional document title

        Returns:
            Tuple of (success, error_message)
            - success: True if PDF was generated successfully
            - error_message: None if successful, error description if failed
        """
        try:
            # Replace diagrams with image references
            processed_text = PDFGenerator._replace_diagrams_with_images(
                markdown_text, diagram_images
            )

            # Create temporary Markdown file
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".md", delete=False
            ) as temp_md:
                # Add title if provided
                if title:
                    temp_md.write(f"% {title}\n\n")
                temp_md.write(processed_text)
                temp_md.flush()

                # Build Pandoc command
                cmd = [
                    "pandoc",
                    temp_md.name,
                    "-o",
                    str(output_file),
                    "--pdf-engine=xelatex",
                    "--standalone",
                    "-V",
                    "geometry:margin=1in",
                    "-V",
                    "documentclass:article",
                    "-V",
                    "papersize:a4",
                ]

                # Run Pandoc
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False,
                )
                if result.returncode != 0:
                    return False, f"Pandoc error: {result.stderr}"

                return True, None

        except subprocess.CalledProcessError as e:
            return False, f"Failed to run Pandoc: {e!s}"
        except Exception as e:
            return False, f"Error generating PDF: {e!s}"
        finally:
            # Clean up temporary file
            if "temp_md" in locals():
                temp_md.close()
                Path(temp_md.name).unlink(missing_ok=True)
