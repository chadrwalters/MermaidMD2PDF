# MermaidMD2PDF API Examples

This document provides detailed examples of using the MermaidMD2PDF API in various scenarios.

## Basic Usage

### Simple Conversion

```python
from pathlib import Path
from mermaidmd2pdf import convert_markdown_to_pdf

# Convert a simple document
convert_markdown_to_pdf(
    input_file=Path("document.md"),
    output_file=Path("output.pdf")
)
```

### With Custom Title

```python
from pathlib import Path
from mermaidmd2pdf import convert_markdown_to_pdf

# Convert with custom title
convert_markdown_to_pdf(
    input_file=Path("document.md"),
    output_file=Path("output.pdf"),
    title="My Technical Documentation"
)
```

## Advanced Usage

### Using Individual Components

```python
from pathlib import Path
from mermaidmd2pdf import (
    FileValidator,
    DependencyChecker,
    MermaidProcessor,
    ImageGenerator,
    PDFGenerator
)

# Initialize components
validator = FileValidator()
checker = DependencyChecker()
processor = MermaidProcessor()
image_gen = ImageGenerator()
pdf_gen = PDFGenerator()

# Check dependencies
checker.check_system_dependencies()
checker.check_python_dependencies()

# Validate files
input_path = Path("document.md")
output_path = Path("output.pdf")
validator.validate_input_file(input_path)
validator.validate_output_file(output_path)

# Process document
with open(input_path) as f:
    content = f.read()

# Extract and validate diagrams
diagrams = processor.extract_diagrams(content)
for diagram in diagrams:
    processor.validate_diagram(diagram)

# Generate images
for i, diagram in enumerate(diagrams):
    image_path = output_path.parent / f"diagram_{i}.png"
    image_gen.generate_image(diagram, image_path)

# Generate PDF
pdf_gen.generate_pdf(
    markdown_path=input_path,
    output_path=output_path,
    title="My Document"
)
```

### Error Handling

```python
from pathlib import Path
from mermaidmd2pdf import (
    convert_markdown_to_pdf,
    MermaidMD2PDFError,
    DependencyError,
    FileValidationError,
    DiagramError,
    PDFGenerationError
)

def convert_document(input_file: Path, output_file: Path) -> None:
    try:
        convert_markdown_to_pdf(input_file, output_file)
    except DependencyError as e:
        print(f"Missing dependencies: {e}")
        # Handle missing dependencies
    except FileValidationError as e:
        print(f"File validation failed: {e}")
        # Handle file validation errors
    except DiagramError as e:
        print(f"Diagram processing failed: {e}")
        # Handle diagram processing errors
    except PDFGenerationError as e:
        print(f"PDF generation failed: {e}")
        # Handle PDF generation errors
    except MermaidMD2PDFError as e:
        print(f"Unexpected error: {e}")
        # Handle other errors
```

### Configuration

```python
import os
from pathlib import Path
from mermaidmd2pdf import convert_markdown_to_pdf

# Configure temporary directory
os.environ["MERMAIDMD2PDF_TEMP_DIR"] = "/tmp/mermaidmd2pdf"

# Configure logging
os.environ["MERMAIDMD2PDF_LOG_LEVEL"] = "DEBUG"

# Convert document
convert_markdown_to_pdf(
    input_file=Path("document.md"),
    output_file=Path("output.pdf")
)
```

## Integration Examples

### With FastAPI

```python
from fastapi import FastAPI, UploadFile, File
from pathlib import Path
import tempfile
from mermaidmd2pdf import convert_markdown_to_pdf

app = FastAPI()

@app.post("/convert")
async def convert_document(file: UploadFile = File(...)):
    # Create temporary files
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as input_file:
        content = await file.read()
        input_file.write(content)
        input_file.flush()

        output_file = Path(input_file.name).with_suffix(".pdf")

        try:
            # Convert document
            convert_markdown_to_pdf(
                input_file=Path(input_file.name),
                output_file=output_file
            )

            # Read generated PDF
            with open(output_file, "rb") as f:
                pdf_content = f.read()

            return Response(
                content=pdf_content,
                media_type="application/pdf",
                headers={
                    "Content-Disposition": f"attachment; filename={output_file.name}"
                }
            )
        finally:
            # Cleanup
            Path(input_file.name).unlink()
            output_file.unlink()
```

### With Django

```python
from django.http import FileResponse
from django.views import View
from pathlib import Path
import tempfile
from mermaidmd2pdf import convert_markdown_to_pdf

class ConvertDocumentView(View):
    def post(self, request):
        # Get uploaded file
        markdown_file = request.FILES["document"]

        # Create temporary files
        with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as input_file:
            for chunk in markdown_file.chunks():
                input_file.write(chunk)
            input_file.flush()

            output_file = Path(input_file.name).with_suffix(".pdf")

            try:
                # Convert document
                convert_markdown_to_pdf(
                    input_file=Path(input_file.name),
                    output_file=output_file
                )

                # Return PDF
                return FileResponse(
                    open(output_file, "rb"),
                    content_type="application/pdf",
                    as_attachment=True,
                    filename=output_file.name
                )
            finally:
                # Cleanup
                Path(input_file.name).unlink()
                output_file.unlink()
```

### With Flask

```python
from flask import Flask, request, send_file
from pathlib import Path
import tempfile
from mermaidmd2pdf import convert_markdown_to_pdf

app = Flask(__name__)

@app.route("/convert", methods=["POST"])
def convert_document():
    if "document" not in request.files:
        return "No file uploaded", 400

    file = request.files["document"]

    # Create temporary files
    with tempfile.NamedTemporaryFile(suffix=".md", delete=False) as input_file:
        file.save(input_file.name)
        input_file.flush()

        output_file = Path(input_file.name).with_suffix(".pdf")

        try:
            # Convert document
            convert_markdown_to_pdf(
                input_file=Path(input_file.name),
                output_file=output_file
            )

            # Return PDF
            return send_file(
                output_file,
                mimetype="application/pdf",
                as_attachment=True,
                download_name=output_file.name
            )
        finally:
            # Cleanup
            Path(input_file.name).unlink()
            output_file.unlink()
```
