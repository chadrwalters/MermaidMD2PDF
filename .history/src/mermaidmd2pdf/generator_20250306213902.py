"""Image generator component for MermaidMD2PDF."""
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from mermaidmd2pdf.processor import MermaidDiagram


class ImageGenerator:
    """Generates images from Mermaid diagrams."""

    @staticmethod
    def _create_mermaid_config() -> Dict[str, any]:
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
            # Create temporary files for diagram and config
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".mmd", delete=False
            ) as mmd_file, tempfile.NamedTemporaryFile(
                mode="w", suffix=".json", delete=False
            ) as config_file:
                # Write diagram content
                mmd_file.write(diagram.content)
                mmd_file.flush()

                # Write config
                json.dump(ImageGenerator._create_mermaid_config(), config_file)
                config_file.flush()

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
                        config_file.name,
                    ],
                    capture_output=True,
                    text=True,
                )

                # Clean up temporary files
                os.unlink(mmd_file.name)
                os.unlink(config_file.name)

                if result.returncode != 0:
                    return False, f"Mermaid CLI error: {result.stderr}", None

                return True, None, output_path

        except subprocess.CalledProcessError as e:
            return False, f"Failed to run Mermaid CLI: {str(e)}", None
        except Exception as e:
            return False, f"Error generating image: {str(e)}", None

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
        diagram_images = {}
        errors = []

        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        for diagram in diagrams:
            success, error, image_path = ImageGenerator.generate_image(diagram, output_dir)
            if success and image_path:
                diagram_images[diagram] = image_path
            if error:
                errors.append(
                    f"Failed to generate image for diagram at line {diagram.start_line}: {error}"
                )

        return diagram_images, errors
