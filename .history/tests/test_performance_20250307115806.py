import os
import shutil
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Generator

import psutil
import pytest

from mermaidmd2pdf.dependencies import DependencyChecker
from mermaidmd2pdf.generator import PDFGenerator
from mermaidmd2pdf.processor import MermaidProcessor
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
flowchart LR
    A[Start] --> B{Decision}
    B -->|Yes| C[Action 1]
    B -->|No| D[Action 2]
    C --> E[End]
    D --> E
```

## Section 5
```mermaid
classDiagram
    class Animal {
        +name: string
        +age: int
        +makeSound()
        +move()
    }
```

## Section 6
```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Processing: Start
    Processing --> Success: Complete
    Processing --> Error: Fail
    Success --> [*]
    Error --> [*]
```
"""

@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """Create a temporary directory for test files."""
    with tempfile.TemporaryDirectory() as tmp_dir:
        yield Path(tmp_dir)

def get_memory_usage() -> float:
    """Get current memory usage in MB."""
    process = psutil.Process()
    return process.memory_info().rss / 1024 / 1024

def measure_execution_time(func):
    """Decorator to measure execution time of a function."""
    def wrapper(*args, **kwargs):
        start_time = time.time()
        start_memory = get_memory_usage()
        result = func(*args, **kwargs)
        end_time = time.time()
        end_memory = get_memory_usage()
        return result, end_time - start_time, end_memory - start_memory
    return wrapper

@measure_execution_time
def process_document(input_path: Path, output_path: Path) -> None:
    """Process a document from markdown to PDF."""
    validator = FileValidator()
    processor = MermaidProcessor()
    generator = PDFGenerator()

    # Validate input
    validator.validate_input(input_path)

    # Process document
    diagrams = processor.process_file(input_path)

    # Generate PDF
    generator.generate_pdf(input_path, output_path, diagrams)

def test_small_document_performance(temp_dir: Path):
    """Test performance with a small document."""
    input_path = temp_dir / "small.md"
    output_path = temp_dir / "small.pdf"

    input_path.write_text(SMALL_DOC)

    _, execution_time, memory_usage = process_document(input_path, output_path)

    # Performance assertions
    assert execution_time < 2.0  # Should process in under 2 seconds
    assert memory_usage < 100.0  # Should use less than 100MB memory
    assert output_path.exists()

def test_medium_document_performance(temp_dir: Path):
    """Test performance with a medium-sized document."""
    input_path = temp_dir / "medium.md"
    output_path = temp_dir / "medium.pdf"

    input_path.write_text(MEDIUM_DOC)

    _, execution_time, memory_usage = process_document(input_path, output_path)

    # Performance assertions
    assert execution_time < 5.0  # Should process in under 5 seconds
    assert memory_usage < 200.0  # Should use less than 200MB memory
    assert output_path.exists()

def test_large_document_performance(temp_dir: Path):
    """Test performance with a large document."""
    input_path = temp_dir / "large.md"
    output_path = temp_dir / "large.pdf"

    input_path.write_text(LARGE_DOC)

    _, execution_time, memory_usage = process_document(input_path, output_path)

    # Performance assertions
    assert execution_time < 10.0  # Should process in under 10 seconds
    assert memory_usage < 500.0  # Should use less than 500MB memory
    assert output_path.exists()

def test_concurrent_processing(temp_dir: Path):
    """Test concurrent processing of multiple documents."""
    documents = [
        ("small.md", SMALL_DOC),
        ("medium.md", MEDIUM_DOC),
        ("large.md", LARGE_DOC)
    ]

    # Create test files
    for filename, content in documents:
        (temp_dir / filename).write_text(content)

    def process_single_doc(filename: str) -> tuple[str, float, float]:
        input_path = temp_dir / filename
        output_path = temp_dir / f"{filename.replace('.md', '.pdf')}"
        return process_document(input_path, output_path)

    # Process documents concurrently
    start_time = time.time()
    with ThreadPoolExecutor(max_workers=3) as executor:
        results = list(executor.map(
            lambda x: process_single_doc(x[0]),
            documents
        ))
    total_time = time.time() - start_time

    # Performance assertions
    assert total_time < 15.0  # Should process all documents in under 15 seconds
    assert all(output_path.exists() for _, _, output_path in results)

def test_memory_cleanup(temp_dir: Path):
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
    assert current_memory < 100.0  # Should clean up to under 100MB
