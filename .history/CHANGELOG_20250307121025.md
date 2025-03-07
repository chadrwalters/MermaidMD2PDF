# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup
- Core functionality for Markdown to PDF conversion
- Support for Mermaid diagrams
- Command-line interface
- Python API
- Comprehensive test suite
- User and API documentation

### Changed
- Switched from WeasyPrint to XeLaTeX for PDF generation
- Improved error handling and validation
- Enhanced performance for large documents

### Fixed
- Memory cleanup issues
- Concurrent processing return values
- PDF engine configuration

### Security
- Added path traversal prevention
- Implemented file permission validation
- Added secure temporary file handling

## [0.1.0] - 2024-03-07

### Added
- Initial release
- Basic Markdown to PDF conversion
- Mermaid diagram support
- Command-line interface
- Python API
- Documentation
- Test suite
