# PDF Engine Selection

## Overview
MermaidMD2PDF uses XeLaTeX as its PDF generation engine. This document explains the rationale behind this choice and provides information about configuration and usage.

## Why XeLaTeX?

After evaluating various PDF generation engines, including WeasyPrint and XeLaTeX, we chose XeLaTeX for the following reasons:

1. **Superior Typography**
   - Industry-standard typesetting algorithms
   - Better handling of complex layouts
   - Professional-quality output

2. **Math and Technical Content**
   - Excellent support for mathematical notation
   - Better handling of technical diagrams
   - Consistent rendering across platforms

3. **Mature Ecosystem**
   - Large collection of available packages
   - Well-documented solutions for common issues
   - Active community support

4. **Complex Layout Support**
   - Better control over page breaks
   - Superior handling of figures and tables
   - More flexible customization options

## Alternative Considered: WeasyPrint

We also evaluated WeasyPrint as a potential PDF engine:

### Pros of WeasyPrint
- Modern CSS-based approach
- Easier integration with web technologies
- Faster processing time
- Simpler setup

### Cons of WeasyPrint
- Limited typographic control
- Poorer math rendering support
- Less mature ecosystem
- Not as good for complex layouts

## Configuration

XeLaTeX configuration can be customized in `pyproject.toml`:

```toml
[tool.mermaidmd2pdf]
pdf_engine = "xelatex"
pdf_engine_opts = [
    "-interaction=nonstopmode",
    "-halt-on-error",
]
template_dir = "templates"
```

### Options
- `pdf_engine`: Specifies the PDF engine (default: "xelatex")
- `pdf_engine_opts`: Additional command-line options for XeLaTeX
- `template_dir`: Directory containing LaTeX templates

## Performance Considerations

While XeLaTeX may be slower than alternatives like WeasyPrint, the performance difference is acceptable given our priorities:
1. Output quality
2. Typography consistency
3. Professional appearance
4. Layout reliability

We've implemented caching mechanisms to mitigate performance impact where possible.
