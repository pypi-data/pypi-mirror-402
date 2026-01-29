# Documentation Build Guide

This directory contains documentation for `rapcsv`, configured for Read the Docs.

## Structure

- `conf.py` - Sphinx configuration file
- `index.rst` - Main documentation index
- `api/index.rst` - API reference documentation
- `*.md` - Markdown documentation files (converted to RST via MyST parser)

## Building Documentation Locally

### Prerequisites

```bash
pip install -e ".[docs]"
```

### Build Documentation

```bash
cd docs
sphinx-build -b html . _build/html
```

The documentation will be available in `docs/_build/html/index.html`.

### View Documentation

Open `docs/_build/html/index.html` in your browser.

## Read the Docs Configuration

The project is configured for Read the Docs via `.readthedocs.yml` in the project root.

### Configuration Files

- `.readthedocs.yml` - Read the Docs build configuration
- `docs/conf.py` - Sphinx configuration
- `docs/index.rst` - Main documentation entry point

## Docstring Format

All docstrings use **Google-style** format for Sphinx compatibility:

```python
def function(param1: str, param2: int = 0) -> bool:
    """Short description.

    Longer description if needed.

    Args:
        param1: Description of param1.
        param2: Description of param2 (default: 0).

    Returns:
        Description of return value.

    Raises:
        ValueError: When something goes wrong.

    Examples:
        .. code-block:: python

            result = function("test", 42)
            print(result)
    """
```

## Extensions Used

- `sphinx.ext.autodoc` - Automatic API documentation from docstrings
- `sphinx.ext.napoleon` - Google-style docstring support
- `sphinx.ext.viewcode` - Source code links
- `myst_parser` - Markdown file support
- `sphinx.ext.intersphinx` - Cross-references to Python docs

## Theme

The documentation uses the `sphinx_rtd_theme` (Read the Docs theme) for consistent styling.
