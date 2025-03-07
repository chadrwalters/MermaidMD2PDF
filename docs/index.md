# MermaidMD2PDF

Convert Markdown files with Mermaid diagrams to beautiful PDFs.

## Features

- **Markdown Support**: Convert any Markdown file to PDF
- **Mermaid Integration**: Automatically renders Mermaid diagrams
- **Customizable**: Configure PDF output settings
- **CLI & API**: Use as a command-line tool or Python library
- **Framework Integration**: Works with FastAPI, Django, and Flask

## Quick Start

### Installation

```bash
pip install mermaidmd2pdf
```

### Basic Usage

```bash
mermaidmd2pdf input.md output.pdf
```

### Python API

```python
from mermaidmd2pdf import convert_to_pdf

convert_to_pdf("input.md", "output.pdf")
```

## Documentation

- [User Guide](user-guide/README.md) - Get started with MermaidMD2PDF
- [API Reference](api-reference/README.md) - Detailed API documentation
- [Examples](examples/README.md) - Example usage and templates

## Requirements

- Python 3.8+
- Pandoc
- Mermaid CLI (mmdc)
- XeLaTeX

## Contributing

We welcome contributions! Please see our [GitHub repository](https://github.com/chadrwalters/MermaidMD2PDF) for details on how to contribute.

## License

This project is licensed under the MIT License - see the LICENSE file for details.
