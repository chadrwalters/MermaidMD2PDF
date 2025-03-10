"""Performance tests for MermaidMD2PDF."""

import tempfile
import time
from collections.abc import Callable
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Any, List, Tuple, TypeVar

import psutil
import pytest

from mermaidmd2pdf.cli import main
from mermaidmd2pdf.dependencies import DependencyChecker
from mermaidmd2pdf.generator import ImageGenerator, PDFGenerator
from mermaidmd2pdf.processor import MermaidProcessor
from mermaidmd2pdf.typing import PathGenerator
from mermaidmd2pdf.validator import FileValidator

# Test data
SMALL_DOC = """# Small Test Document

```mermaid
graph TD
    A[Start] --> B[Process]
    B --> C[End]
```
"""

MEDIUM_DOC = """# Medium Test Document

## Section 1
```mermaid
graph TD
    A[Start] --> B[Process]
    B --> C[End]
```

## Section 2
```mermaid
sequenceDiagram
    participant A
    participant B
    A->>B: Hello
    B->>A: Hi there
```

## Section 3
```mermaid
pie title Test Pie Chart
    "A" : 30
    "B" : 40
    "C" : 30
```
"""

LARGE_DOC = """# Large Test Document

## Introduction
This is a large test document with multiple sections and diagrams.

## Section 1
```mermaid
graph TD
    A[Start] --> B[Process]
    B --> C[End]
```

## Section 2
```mermaid
sequenceDiagram
    participant A
    participant B
    A->>B: Hello
    B->>A: Hi there
```

## Section 3
```mermaid
pie title Test Pie Chart
    "A" : 30
    "B" : 40
    "C" : 30
```

## Section 4
```mermaid
graph LR
    A[Start] --> B{Decision}
    B -->|Yes| C[Action 1]
    B -->|No| D[Action 2]
    C --> E[End]
    D --> E
```

## Section 5
```mermaid
erDiagram
    CUSTOMER ||--o{ ORDER : places
    ORDER ||--|{ LINE_ITEM : contains
```

## Section 6
```mermaid
stateDiagram
    [*] --> Idle
    Idle --> Processing: Start
    Processing --> Success: Complete
    Processing --> Error: Fail
    Success --> [*]
    Error --> [*]
```
"""

# Performance thresholds
SMALL_DOC_TIME_LIMIT = 8.0  # seconds (increased for XeLaTeX startup overhead)
SMALL_DOC_MEMORY_LIMIT = 150.0  # MB (adjusted for XeLaTeX base memory usage)
MEDIUM_DOC_TIME_LIMIT = 12.0  # seconds (increased for multiple diagram processing)
MEDIUM_DOC_MEMORY_LIMIT = 250.0  # MB (adjusted for multiple diagrams)
LARGE_DOC_TIME_LIMIT = 20.0  # seconds (increased for complex document processing)
LARGE_DOC_MEMORY_LIMIT = 400.0  # MB (XeLaTeX is more memory efficient for large docs)
BATCH_TIME_LIMIT = 30.0  # seconds (increased for concurrent XeLaTeX processes)
CLEANUP_MEMORY_LIMIT = 150.0  # MB (adjusted for XeLaTeX cleanup requirements)

# Type variables for the decorator
T = TypeVar("T")
R = TypeVar("R")

# Constants
DIAGRAM_COUNT = 2  # Number of diagrams in test files
CONCURRENT_FILE_COUNT = 5


@pytest.fixture
def temp_dir() -> PathGenerator:
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir)


def get_memory_usage() -> float:
    """Get current memory usage in MB."""
    process = psutil.Process()
    return float(process.memory_info().rss / 1024 / 1024)


def measure_execution_time(
    func: Callable[..., T],
) -> Callable[..., Tuple[T, float, float]]:
    """Decorator to measure execution time of a function."""

    def wrapper(*args: Any, **kwargs: Any) -> Tuple[T, float, float]:
        start_time = time.time()
        start_memory = get_memory_usage()
        result = func(*args, **kwargs)
        end_time = time.time()
        end_memory = get_memory_usage()
        return result, end_time - start_time, end_memory - start_memory

    return wrapper


@measure_execution_time
def process_document(input_path: Path, output_path: Path) -> Path:
    """Process a document from markdown to PDF."""
    validator = FileValidator()
    processor = MermaidProcessor()

    # Validate input and output
    is_valid, error = validator.validate_input_file(str(input_path))
    if not is_valid:
        raise ValueError(f"Input validation failed: {error}")

    is_valid, error = validator.validate_output_file(str(output_path))
    if not is_valid:
        raise ValueError(f"Output validation failed: {error}")

    # Read and process document
    with open(input_path, encoding="utf-8") as f:
        content = f.read()

    # Process markdown and extract diagrams
    processed_text, errors = processor.process_markdown(content)
    if errors:
        raise ValueError(f"Markdown processing failed: {'; '.join(errors)}")

    diagrams = processor.extract_diagrams(content)

    # Create temporary directory for images
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)

        # Generate images for diagrams
        image_generator = ImageGenerator(output_dir=temp_path)
        diagram_images, errors = image_generator.generate_images(diagrams, temp_path)
        if errors:
            raise ValueError(f"Failed to generate images: {'; '.join(errors)}")

        # Generate PDF
        success, error = PDFGenerator.generate_pdf(
            processed_text, diagram_images, output_path, title="MermaidMD2PDF Document"
        )
        if not success:
            raise ValueError(f"PDF generation failed: {error}")

    return output_path


def test_small_document_performance(temp_dir: Path) -> None:
    """Test performance with a small document."""
    input_path = temp_dir / "small.md"
    output_path = temp_dir / "small.pdf"

    input_path.write_text(SMALL_DOC)

    _, execution_time, memory_usage = process_document(input_path, output_path)

    # Performance assertions
    assert (
        execution_time < SMALL_DOC_TIME_LIMIT
    )  # Should process in under 8 seconds (XeLaTeX is slower)
    assert memory_usage < SMALL_DOC_MEMORY_LIMIT  # Should use less than 150MB memory
    assert output_path.exists()


def test_medium_document_performance(temp_dir: Path) -> None:
    """Test performance with a medium-sized document."""
    input_path = temp_dir / "medium.md"
    output_path = temp_dir / "medium.pdf"

    input_path.write_text(MEDIUM_DOC)

    _, execution_time, memory_usage = process_document(input_path, output_path)

    # Performance assertions
    assert execution_time < MEDIUM_DOC_TIME_LIMIT  # Should process in under 12 seconds
    assert memory_usage < MEDIUM_DOC_MEMORY_LIMIT  # Should use less than 250MB memory
    assert output_path.exists()


def test_large_document_performance(temp_dir: Path) -> None:
    """Test performance with a large document."""
    input_path = temp_dir / "large.md"
    output_path = temp_dir / "large.pdf"

    input_path.write_text(LARGE_DOC)

    _, execution_time, memory_usage = process_document(input_path, output_path)

    # Performance assertions
    assert execution_time < LARGE_DOC_TIME_LIMIT  # Should process in under 20 seconds
    assert memory_usage < LARGE_DOC_MEMORY_LIMIT  # Should use less than 400MB memory
    assert output_path.exists()


def test_concurrent_processing(temp_dir: Path) -> None:
    """Test concurrent processing of multiple documents."""
    documents = [
        ("small.md", SMALL_DOC),
        ("medium.md", MEDIUM_DOC),
        ("large.md", LARGE_DOC),
    ]

    # Create test files
    for filename, content in documents:
        (temp_dir / filename).write_text(content)

    def process_single_doc(filename: str) -> Tuple[Path, float, float]:
        input_path = temp_dir / filename
        output_path = temp_dir / f"{filename.replace('.md', '.pdf')}"
        return process_document(input_path, output_path)

    # Process documents concurrently
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(lambda x: process_single_doc(x[0]), documents))
    total_time = time.time() - start_time

    # Performance assertions
    assert total_time < BATCH_TIME_LIMIT
    assert all(output_path.exists() for output_path, _, _ in results)


def test_memory_cleanup(temp_dir: Path) -> None:
    """Test memory cleanup after processing."""
    input_path = temp_dir / "cleanup.md"
    output_path = temp_dir / "cleanup.pdf"

    input_path.write_text(LARGE_DOC)

    # Process document
    _, _, memory_usage = process_document(input_path, output_path)

    # Force garbage collection
    import gc

    gc.collect()

    # Check memory usage after cleanup
    current_memory = get_memory_usage()
    assert current_memory < CLEANUP_MEMORY_LIMIT  # Should clean up to under 150MB


@pytest.fixture
def temp_output_dir(tmp_path: Path) -> Path:
    """Create a temporary output directory."""
    output_dir = tmp_path / "output"
    output_dir.mkdir()
    return output_dir


@pytest.fixture
def large_markdown_file(temp_output_dir: Path) -> Path:
    """Create a large markdown file with multiple diagrams."""
    markdown_file = temp_output_dir / "large.md"
    content = ["# Large Document\n\n"]

    # Add multiple diagrams
    for i in range(DIAGRAM_COUNT):
        content.append(f"\n## Section {i + 1}\n\n")
        content.append("```mermaid\n")
        content.append("graph TD\n")
        content.append(f"A{i}[Start] --> B{i}[Process]\n")
        content.append(f"B{i} --> C{i}[End]\n")
        content.append("```\n\n")
        content.append(f"Some text for section {i + 1}\n\n")

    markdown_file.write_text("".join(content))
    return markdown_file


def test_performance_with_large_file(
    temp_output_dir: Path, large_markdown_file: Path
) -> None:
    """Test performance with a large markdown file containing multiple diagrams."""
    # Check dependencies
    checker = DependencyChecker()
    deps_ok, error = checker.verify_all()
    assert deps_ok, f"Dependencies not satisfied: {error}"

    # Validate input and output files
    validator = FileValidator()
    output_file = temp_output_dir / "output.pdf"
    assert validator.validate_input_file(str(large_markdown_file))
    assert validator.validate_output_file(str(output_file))

    # Read input file
    markdown_text = large_markdown_file.read_text()

    # Process markdown and extract diagrams
    processor = MermaidProcessor()
    diagrams = processor.extract_diagrams(markdown_text)
    assert len(diagrams) == DIAGRAM_COUNT

    # Generate images
    image_generator = ImageGenerator(output_dir=temp_output_dir)
    diagram_images, errors = image_generator.generate_images(diagrams, temp_output_dir)
    assert not errors, f"Image generation failed: {'; '.join(errors)}"
    assert len(diagram_images) == DIAGRAM_COUNT

    # Create PDF
    success, error = PDFGenerator.generate_pdf(
        markdown_text, diagram_images, output_file, title="Test Document"
    )
    assert success, f"PDF generation failed: {error}"
    assert output_file.exists()


def test_performance_with_concurrent_requests(temp_output_dir: Path) -> None:
    """Test performance with concurrent processing of multiple files."""
    # Create multiple input files
    input_files: List[Path] = []
    for i in range(CONCURRENT_FILE_COUNT):
        markdown_file = temp_output_dir / f"test_{i}.md"
        content = [
            f"# Test Document {i}\n\n",
            "```mermaid\n",
            "graph TD\n",
            f"A{i}[Start] --> B{i}[Process]\n",
            f"B{i} --> C{i}[End]\n",
            "```\n\n",
            f"Some text for document {i}\n",
        ]
        markdown_file.write_text("".join(content))
        input_files.append(markdown_file)

    # Check dependencies
    checker = DependencyChecker()
    deps_ok, error = checker.verify_all()
    assert deps_ok, f"Dependencies not satisfied: {error}"

    # Measure processing time
    start_time = time.time()

    # Process each file
    for i, input_file in enumerate(input_files):
        output_file = temp_output_dir / f"output_{i}.pdf"
        success = main.main([str(input_file), str(output_file)], standalone_mode=False)
        assert success is None  # Click commands return None on success
        assert output_file.exists()

    # Calculate total time
    total_time = time.time() - start_time
    print(f"\nProcessing time for concurrent files: {total_time:.2f} seconds")
