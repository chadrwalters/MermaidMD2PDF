"""Image and PDF generator components for MermaidMD2PDF."""

import os
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from mermaidmd2pdf.processor import MermaidDiagram


class ImageGenerator:
    """Generates images from Mermaid diagrams."""

    @staticmethod
    def _create_mermaid_config() -> Dict[str, Any]:
        """Create default Mermaid configuration.

        Returns:
            Dictionary containing Mermaid configuration
        """
        return {
            "theme": "default",
            "themeVariables": {
                "fontFamily": "arial",
                "fontSize": "14px",
            },
        }

    @staticmethod
    def _create_puppeteer_config() -> Dict[str, Any]:
        """Create Puppeteer configuration.

        Returns:
            Dictionary containing Puppeteer configuration
        """
        return {"args": ["--no-sandbox", "--disable-setuid-sandbox"]}

    @staticmethod
    def generate_image(
        diagram: MermaidDiagram, output_dir: Path
    ) -> Tuple[bool, Optional[str], Optional[Path]]:
        """Generate an image from a Mermaid diagram.

        Args:
            diagram: The MermaidDiagram to convert
            output_dir: Directory to save the generated image

        Returns:
            Tuple of (success, error_message, image_path)
            - success: True if image was generated successfully
            - error_message: None if successful, error description if failed
            - image_path: Path to generated image if successful, None if failed
        """
        try:
            # Create unique filename for this diagram
            output_file = output_dir / f"diagram_{hash(diagram.content)}.png"

            # Get path to mermaid config file
            config_path = Path(__file__).parent / "mermaid-config.json"
            if not config_path.exists():
                return False, "Mermaid config file not found", None

            # Create temporary file for diagram content
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".mmd", delete=False
            ) as mmd_file:
                mmd_file.write(diagram.content)
                mmd_file.flush()

                cmd = [
                    "mmdc",
                    "-i",
                    str(mmd_file.name),
                    "-o",
                    str(output_file),
                    "--scale",
                    "2",
                    "--backgroundColor",
                    "white",
                    "--configFile",
                    str(config_path),
                ]

                # Run mmdc (Mermaid CLI)
                result = subprocess.run(cmd, check=True, capture_output=True, text=True)

                # Clean up temporary file
                os.unlink(mmd_file.name)

                if result.stderr and "error" in result.stderr.lower():
                    print(f"⚠️  Warning: {result.stderr.strip()}")

                if output_file.exists() and output_file.stat().st_size > 0:
                    return True, None, output_file
                else:
                    return False, "Generated image file is empty or missing", None

        except subprocess.CalledProcessError as e:
            error_msg = f"Failed to generate image: {e.stderr if e.stderr else str(e)}"
            return False, error_msg, None
        except Exception as e:
            error_msg = f"Unexpected error: {e!s}"
            return False, error_msg, None

    @staticmethod
    def generate_images(
        diagrams: List[MermaidDiagram], output_dir: Path
    ) -> Tuple[Dict[MermaidDiagram, Path], List[str]]:
        """Generate images for multiple Mermaid diagrams.

        Args:
            diagrams: List of MermaidDiagrams to convert
            output_dir: Directory to save the generated images

        Returns:
            Tuple of (diagram_images, errors)
            - diagram_images: Dictionary mapping diagrams to their image paths
            - errors: List of error messages for failed conversions
        """
        # Return early if there are no diagrams to process
        if not diagrams:
            return {}, []

        diagram_images = {}
        errors = []
        total_diagrams = len(diagrams)

        print(
            "\n🔄 Processing "
            f"{total_diagrams} Mermaid diagram{'s' if total_diagrams > 1 else ''}..."
        )

        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # Process diagrams in parallel
        with ThreadPoolExecutor(
            max_workers=min(len(diagrams), os.cpu_count() or 1)
        ) as executor:
            future_to_diagram = {
                executor.submit(
                    ImageGenerator.generate_image, diagram, output_dir
                ): diagram
                for diagram in diagrams
            }

            completed = 0
            for future in as_completed(future_to_diagram):
                diagram = future_to_diagram[future]
                completed += 1
                try:
                    success, error, image_path = future.result()
                    if success and image_path:
                        diagram_images[diagram] = image_path
                        print(
                            f"✅ Generated diagram {completed}/{total_diagrams} "
                            f"(line {diagram.start_line})"
                        )
                    if error:
                        errors.append(
                            f"Error in diagram at line {diagram.start_line}: {error}"
                        )
                        print(
                            "❌ Failed to generate diagram "
                            f"{completed}/{total_diagrams} "
                            f"(line {diagram.start_line})"
                        )
                except Exception as e:
                    errors.append(
                        f"Error in diagram at line {diagram.start_line}: {e!s}"
                    )
                    print(
                        "❌ Failed to generate diagram "
                        f"{completed}/{total_diagrams} "
                        f"(line {diagram.start_line})"
                    )

        if diagram_images:
            print(
                f"\n✨ Successfully generated {len(diagram_images)}/{total_diagrams} "
                "diagrams"
            )
        if errors:
            print(
                "\n⚠️  Failed to generate "
                f"{len(errors)} diagram{'s' if len(errors) > 1 else ''}"
            )

        return diagram_images, errors

    @staticmethod
    def generate_image_with_config(
        diagram: MermaidDiagram,
        output_dir: Path,
        config_path: str,
        puppeteer_path: str,
    ) -> Tuple[bool, Optional[str], Optional[Path]]:
        """Generate an image from a Mermaid diagram using shared config files.

        Args:
            diagram: The MermaidDiagram to convert
            output_dir: Directory to save the generated image
            config_path: Path to the shared Mermaid config file
            puppeteer_path: Path to the shared Puppeteer config file

        Returns:
            Tuple of (success, error_message, image_path)
            - success: True if successful, False if failed
            - error_message: None if successful, error description if failed
            - image_path: Path to generated image if successful, None if failed
        """
        try:
            # Create temporary file for diagram
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".mmd", delete=False
            ) as mmd_file:
                # Write diagram content
                mmd_file.write(diagram.content)
                mmd_file.flush()

                # Generate unique output filename
                output_path = output_dir / f"diagram_{hash(diagram.content)}.svg"

                # Run mmdc (Mermaid CLI)
                result = subprocess.run(
                    [
                        "mmdc",
                        "-i",
                        mmd_file.name,
                        "-o",
                        str(output_path),
                        "-c",
                        config_path,
                        "-p",
                        puppeteer_path,
                    ],
                    capture_output=True,
                    text=True,
                    check=False,
                )

                # Clean up temporary file
                os.unlink(mmd_file.name)

                if result.returncode != 0:
                    return False, f"Mermaid CLI error: {result.stderr}", None

                return True, None, output_path

        except subprocess.CalledProcessError as e:
            return False, f"Failed to run Mermaid CLI: {e!s}", None
        except Exception as e:
            return False, f"Error generating image: {e!s}", None


class PDFGenerator:
    """Generates PDFs from Markdown with embedded Mermaid diagrams."""

    @staticmethod
    def _check_pandoc_available() -> Tuple[bool, Optional[str]]:
        """Check if Pandoc is available in the system.

        Returns:
            Tuple of (available, error_message)
        """
        try:
            subprocess.run(
                ["pandoc", "--version"],
                capture_output=True,
                check=True,
            )
            return True, None
        except FileNotFoundError:
            return False, "PDF generation failed:\n  • Pandoc not found"
        except Exception as e:
            return False, f"PDF generation failed:\n  • Error checking Pandoc: {e}"

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
        except FileNotFoundError as e:
            return False, f"Failed to run Pandoc: {e!s}"
        except Exception as e:
            return False, f"Error generating PDF: {e!s}"
        finally:
            # Clean up temporary file
            if "temp_md" in locals():
                temp_md.close()
                Path(temp_md.name).unlink(missing_ok=True)
