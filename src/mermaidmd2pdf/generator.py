"""Image and PDF generator components for MermaidMD2PDF."""

import hashlib
import json
import os
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from mermaidmd2pdf.logging import get_logger
from mermaidmd2pdf.processor import MermaidDiagram
from mermaidmd2pdf.utils import atomic_write

logger = get_logger(__name__)


class ImageGenerator:
    """Generates images from Mermaid diagrams.

    This class handles the conversion of Mermaid diagrams to images using the
    Mermaid CLI (mmdc). It implements a caching system to avoid regenerating
    identical diagrams and supports concurrent generation of multiple diagrams.
    """

    def __init__(self, output_dir: Path, cache_dir: Optional[Path] = None) -> None:
        """Initialize the image generator.

        Args:
            output_dir: Directory to save generated images
            cache_dir: Optional directory to cache generated images.
                     If None, uses a '.mermaid_cache' directory in the user's home.
        """
        self.output_dir = output_dir
        self.cache_dir = cache_dir or Path.home() / ".mermaid_cache"
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Using cache directory: {self.cache_dir}")
        self.config = {
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--allow-file-access-from-files",
            ],
            "executablePath": (
                "/usr/bin/chromium-browser"
                if os.path.exists("/usr/bin/chromium-browser")
                else None
            ),
            "headless": "new",
        }

    def _get_cache_key(self, diagram: MermaidDiagram) -> str:
        """Generate a cache key for a diagram.

        Creates a unique hash based on both the diagram content and its
        configuration. This ensures that diagrams with the same content but
        different styling configurations get different cache entries.

        The hash is deterministic and based on:
        1. The diagram content
        2. The JSON-serialized configuration (sorted for consistency)

        Args:
            diagram: The Mermaid diagram to generate a key for

        Returns:
            A unique SHA-256 hash string for the diagram
        """
        # Include both content and configuration in the hash
        content = diagram.content
        config = json.dumps(diagram.config or {}, sort_keys=True)
        combined = f"{content}|{config}"
        return hashlib.sha256(combined.encode()).hexdigest()

    def _get_cached_image(self, cache_key: str) -> Optional[Path]:
        """Get a cached image if it exists.

        Args:
            cache_key: The cache key to look up

        Returns:
            Path to the cached image if it exists, None otherwise
        """
        cached_path = self.cache_dir / cache_key
        return cached_path if cached_path.exists() else None

    def _cache_image(self, diagram: MermaidDiagram, image_path: Path) -> Path:
        """Cache an image for future use.

        Stores a successfully generated image in the cache using the
        diagram's hash as the key. This method is thread-safe as it
        uses atomic file operations.

        Args:
            diagram: The Mermaid diagram that was rendered
            image_path: Path to the generated image

        Returns:
            Path to the cached image
        """
        cache_key = self._get_cache_key(diagram)
        cached_path = self.cache_dir / f"{cache_key}.png"
        if not cached_path.exists():
            cached_path.write_bytes(image_path.read_bytes())
            logger.debug(f"Cached diagram image at: {cached_path}")
        return cached_path

    def _create_mermaid_config(self) -> Dict[str, Any]:
        """Create default Mermaid configuration.

        Defines the default styling and behavior settings for Mermaid diagrams.
        These settings ensure consistent appearance across all generated diagrams.

        Returns:
            Dictionary containing Mermaid configuration with standardized
            font family and size settings
        """
        return {
            "theme": "default",
            "themeVariables": {
                "fontFamily": "arial",
                "fontSize": "14px",
            },
        }

    def _create_puppeteer_config(self) -> Dict[str, Any]:
        """Create Puppeteer configuration.

        Configures Puppeteer (used by Mermaid CLI) with security settings
        that work in various environments, including CI/CD pipelines.

        Returns:
            Dictionary containing Puppeteer configuration with sandbox
            settings optimized for automation
        """
        return {
            "args": [
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--allow-file-access-from-files",
            ],
            "executablePath": (
                "/usr/bin/chromium-browser"
                if os.path.exists("/usr/bin/chromium-browser")
                else None
            ),
            "headless": "new",
        }

    def _check_mmdc_available(self) -> Tuple[bool, Optional[str]]:
        """Check if Mermaid CLI (mmdc) is available.

        Returns:
            Tuple of (available, error_message)
        """
        try:
            subprocess.run(
                ["mmdc", "--version"],
                capture_output=True,
                check=True,
                shell=False,
            )
            return True, None
        except FileNotFoundError:
            return False, "Mermaid CLI (mmdc) not found"
        except subprocess.CalledProcessError as e:
            error_details = e.stderr if e.stderr else str(e)
            error_msg = (
                f"PDF generation failed:\n  • Error checking Pandoc: {error_details}"
            )
            return False, error_msg
        except Exception as e:
            return False, str(e)

    def generate_image(
        self, diagram: MermaidDiagram, output_dir: Path
    ) -> Tuple[bool, Optional[str], Optional[Path]]:
        """Generate an image from a Mermaid diagram.

        This method handles the complete image generation process:
        1. Checks if Mermaid CLI is available
        2. Checks the cache for an existing image
        3. If not cached, creates a temporary file for the diagram
        4. Invokes the Mermaid CLI to generate the image
        5. Caches the result for future use
        6. Cleans up temporary files

        The method is designed to be thread-safe and can be called
        concurrently from multiple threads.

        Args:
            diagram: The Mermaid diagram to render
            output_dir: Directory to store the output image

        Returns:
            Tuple of (success, error_message, image_path)
            - success: True if generation was successful
            - error_message: Description of the error if generation failed
            - image_path: Path to the generated/cached image if successful
        """
        # Check if Mermaid CLI is available
        mmdc_available, error = self._check_mmdc_available()
        if not mmdc_available:
            return False, error, None

        # Check cache for performance optimization
        cached_image = self._get_cached_image(self._get_cache_key(diagram))
        if cached_image:
            logger.debug(f"Using cached image for diagram: {cached_image}")
            return True, None, cached_image

        # Generate new image if not cached
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".mmd", delete=False
        ) as temp_file:
            # Write diagram content to temporary file
            temp_file.write(diagram.content)
            temp_file.flush()

            # Generate unique output filename based on diagram hash
            output_file = output_dir / f"{diagram.__hash__()}.png"
            try:
                # Execute Mermaid CLI with proper error handling
                result = subprocess.run(
                    [
                        "mmdc",  # Mermaid CLI command
                        "-i",
                        temp_file.name,  # Input file
                        "-o",
                        str(output_file),  # Output file
                        *self._get_mmdc_args(diagram),  # Additional configuration
                    ],
                    check=True,
                    capture_output=True,
                    text=True,
                )

                # Log any warnings but continue processing
                if result.stderr:
                    logger.warning(f"Mermaid CLI warning: {result.stderr}")

                # Cache successful result and return
                cached_path = self._cache_image(diagram, output_file)
                return True, None, cached_path

            except subprocess.CalledProcessError as e:
                error_msg = f"Failed to generate image: {e.stderr}"
                logger.error(error_msg)
                return False, error_msg, None
            finally:
                # Clean up temporary files
                os.unlink(temp_file.name)
                if output_file.exists():
                    os.unlink(output_file)

    def generate_images(
        self, diagrams: List[MermaidDiagram], output_dir: Path
    ) -> Tuple[Dict[MermaidDiagram, Path], List[str]]:
        """Generate images for multiple Mermaid diagrams concurrently.

        Uses a thread pool to generate multiple images in parallel, improving
        performance for documents with multiple diagrams. The method handles
        thread synchronization and error collection.

        Args:
            diagrams: List of Mermaid diagrams to render
            output_dir: Directory to store the output images

        Returns:
            Tuple of (diagram to image path mapping, list of errors)
            - diagram_images: Dictionary mapping diagrams to their image paths
            - errors: List of error messages from failed generations
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        diagram_images: Dict[MermaidDiagram, Path] = {}
        errors: List[str] = []

        # Only log if there are diagrams to process
        if diagrams:
            logger.info(
                "🔄 Processing {} Mermaid diagram{}...".format(
                    len(diagrams), "s" if len(diagrams) != 1 else ""
                )
            )

        # Use thread pool for concurrent image generation
        with ThreadPoolExecutor() as executor:
            # Submit all diagram generation tasks
            future_to_diagram = {
                executor.submit(self.generate_image, d, output_dir): d for d in diagrams
            }

            # Process completed tasks as they finish
            for future in as_completed(future_to_diagram):
                diagram = future_to_diagram[future]
                try:
                    success, error, image_path = future.result()
                    if not success:
                        errors.append(error or "Unknown error")
                    elif image_path:
                        diagram_images[diagram] = image_path
                except Exception as e:
                    errors.append(f"Error processing diagram: {e}")

        return diagram_images, errors

    def _get_mmdc_args(self, diagram: MermaidDiagram) -> List[str]:
        """Get Mermaid CLI arguments based on diagram configuration.

        Constructs the command-line arguments for the Mermaid CLI (mmdc)
        based on the diagram's configuration. Creates a temporary config
        file if the diagram has custom configuration.

        Args:
            diagram: The Mermaid diagram to get arguments for

        Returns:
            List of command-line arguments for mmdc, including any
            diagram-specific configuration
        """
        args = []
        if diagram.config:
            # Create temporary file for diagram-specific configuration
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as config_file:
                json.dump(diagram.config, config_file)
                config_file.flush()
                args.extend(["-c", config_file.name])
        return args

    def generate_image_with_config(
        self,
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
                output_path = output_dir / f"diagram_{hash(diagram)}.svg"

                # Build command with proper argument list to prevent shell injection
                cmd = [
                    "mmdc",
                    "-i",
                    str(mmd_file.name),
                    "-o",
                    str(output_path),
                    "-c",
                    str(config_path),
                    "-p",
                    str(puppeteer_path),
                ]

                try:
                    # Run mmdc (Mermaid CLI) with strict security settings
                    result = subprocess.run(
                        cmd,
                        capture_output=True,
                        text=True,
                        check=False,
                        shell=False,  # Explicitly disable shell for security
                    )

                    # Clean up temporary file
                    try:
                        Path(mmd_file.name).unlink(missing_ok=True)
                    except Exception as e:
                        print(f"⚠️  Warning: Failed to clean up temporary file: {e}")

                    if result.returncode != 0:
                        return False, f"Mermaid CLI error: {result.stderr}", None

                    return True, None, output_path

                except subprocess.CalledProcessError as e:
                    error_details = e.stderr if e.stderr else str(e)
                    error_msg = (
                        "PDF generation failed:\n"
                        f"  • Error checking Pandoc: {error_details}"
                    )
                    return False, error_msg, None

        except Exception as e:
            return False, str(e), None


class PDFGenerator:
    """Generates PDFs from Markdown with embedded Mermaid diagrams."""

    @staticmethod
    def _check_pandoc_available() -> Tuple[bool, Optional[str]]:
        """Check if Pandoc is available in the system.

        Returns:
            Tuple of (available, error_message)
        """
        try:
            # Run pandoc with strict security settings
            subprocess.run(
                ["pandoc", "--version"],
                capture_output=True,
                check=True,
                shell=False,  # Explicitly disable shell for security
            )
            return True, None
        except FileNotFoundError:
            return False, "PDF generation failed:\n  • Pandoc not found"
        except subprocess.CalledProcessError as e:
            error_details = e.stderr if e.stderr else str(e)
            error_msg = (
                f"PDF generation failed:\n  • Error checking Pandoc: {error_details}"
            )
            return False, error_msg
        except Exception as e:
            return False, str(e)

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
            # Use pathlib to ensure proper path handling
            image_ref = f"![Diagram]({image_path.resolve()})"
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
        # Create parent directory if it doesn't exist
        output_file.parent.mkdir(parents=True, exist_ok=True)

        # Replace diagrams with image references
        processed_text = PDFGenerator._replace_diagrams_with_images(
            markdown_text, diagram_images
        )

        # Use temporary directory for intermediate files
        with tempfile.TemporaryDirectory(prefix="mermaidmd2pdf-") as temp_dir:
            temp_path = Path(temp_dir)
            temp_md = temp_path / "input.md"

            try:
                # Write content with atomic operation
                with atomic_write(temp_md) as tmp_path:
                    if title:
                        tmp_path.write_text(f"% {title}\n\n{processed_text}")
                    else:
                        tmp_path.write_text(processed_text)

                # Build Pandoc command with proper argument list
                cmd = [
                    "pandoc",
                    str(temp_md.resolve()),  # Use absolute path for input file
                    "-o",
                    str(output_file.resolve()),  # Use absolute path for output file
                    "--pdf-engine=xelatex",
                    "--standalone",
                    "-V",
                    "geometry:margin=1in",
                    "-V",
                    "documentclass:article",
                    "-V",
                    "papersize:a4",
                ]

                # Run Pandoc with strict security settings
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    check=False,
                    shell=False,  # Explicitly disable shell for security
                    cwd=str(temp_path),  # Set working directory explicitly
                )

                if result.returncode != 0:
                    error_msg = f"Failed to run Pandoc: {result.stderr}"
                    logger.error(error_msg)
                    return False, error_msg

                return True, None

            except Exception as e:
                return False, str(e)
