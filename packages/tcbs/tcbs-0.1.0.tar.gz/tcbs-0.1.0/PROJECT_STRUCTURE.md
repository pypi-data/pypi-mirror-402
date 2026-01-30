# TCBS Python SDK - Project Structure

## Directory Layout

```
tcbs-python-sdk/
├── tcbs/                      # Main package directory
│   ├── __init__.py           # Package initialization, exports
│   ├── client.py             # Main TCBSClient class
│   ├── auth.py               # Authentication and token management
│   └── exceptions.py         # Custom exceptions
│
├── examples/                  # Usage examples (not included in package)
│   ├── README.md             # Examples documentation
│   ├── basic_usage.py        # Getting started example
│   └── market_data.py        # Market data queries
│
├── tests/                     # Unit tests (create when needed)
│   └── test_client.py
│
├── docs/                      # Additional documentation (optional)
│
├── setup.py                   # Package setup configuration
├── pyproject.toml            # Modern Python project metadata
├── MANIFEST.in               # Files to include in distribution
├── requirements.txt          # Runtime dependencies
├── README.md                 # Main documentation (bilingual)
├── LICENSE                   # MIT License
├── CHANGELOG.md              # Version history
├── CONTRIBUTING.md           # Contribution guidelines
├── PUBLISHING.md             # PyPI publishing guide
├── .gitignore                # Git exclusions
├── check_package.py          # Pre-publish validation script
│
└── [Development files - not published]
    ├── .key                  # API key (gitignored)
    ├── example.py            # Development examples
    ├── test_api_key.py       # API key tests
    ├── Untitled.ipynb        # Jupyter notebooks
    └── openapi.json          # API specification
```

## Package Files (Published to PyPI)

These files are included in the PyPI distribution:

- `tcbs/` - All Python files in the package
- `README.md` - Package documentation
- `LICENSE` - MIT License
- `requirements.txt` - Dependencies
- `pyproject.toml` - Project metadata

## Development Files (Not Published)

These files are excluded from PyPI (via MANIFEST.in and .gitignore):

- `.key`, `*.key` - API keys
- `example.py` - Development examples
- `test_api_key.py` - Test scripts with keys
- `*.ipynb` - Jupyter notebooks
- `openapi.json` - API specs
- `__pycache__/`, `*.pyc` - Python cache
- `build/`, `dist/`, `*.egg-info/` - Build artifacts

## Key Configuration Files

### setup.py
Traditional setuptools configuration. Reads version from `tcbs/__init__.py`.

### pyproject.toml
Modern Python project configuration (PEP 518). Preferred for new projects.

### MANIFEST.in
Specifies which non-Python files to include in the distribution.

### .gitignore
Prevents sensitive files and build artifacts from being committed.

## Version Management

Version is defined in one place: `tcbs/__init__.py`

```python
__version__ = "0.1.0"
```

Both `setup.py` and `pyproject.toml` read from this file.

## Publishing Workflow

1. Update version in `tcbs/__init__.py`
2. Update `CHANGELOG.md`
3. Run `python check_package.py` to validate
4. Build: `python -m build`
5. Test on Test PyPI
6. Publish to PyPI
7. Create git tag

See `PUBLISHING.md` for detailed instructions.
