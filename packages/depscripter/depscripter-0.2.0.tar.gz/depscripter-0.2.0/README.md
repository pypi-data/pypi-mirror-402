# depscripter

depscripter is a zero-dependency CLI tool and library that automatically adds [PEP 723](https://peps.python.org/pep-0723/) inline script metadata to Python scripts. It scans imports, resolves installed versions from the current environment, and injects the appropriate metadata block.

## Installation

Using [uv](https://github.com/astral-sh/uv):

```bash
uv tool install depscripter
# or run directly
uv run depscripter script.py
```

## Usage

### CLI

Pass the path to a python script to generate the metadata. By default, it prints to stdout.

```bash
# Preview changes
depscripter script.py

# Modify the file in-place
depscripter script.py --in-place

# Save output to a specific file
depscripter script.py -o output.py

# Specify python version requirement
depscripter script.py --python ">=3.9"

# Manually specify dependencies (override or add)
depscripter script.py --manual "numpy>=2.0" --manual "pandas"

# Disable version pinning (just list packages)
depscripter script.py --no-pin
```

The tool will:
1. Parse the script to find imports (ignoring relative imports).
2. Look up the installed package for each import in the **current environment**.
3. Generate a PEP 723 metadata block.
4. Insert it at the top of the script (preserving shebangs and encoding cookies).

### Library

You can also use `depscripter` as a library:

```python
from depscripter import scan_imports, resolve_packages, generate_script_metadata

code = "import requests"
modules = scan_imports(code)
# {'requests'}

deps = resolve_packages(modules, pin_versions=True)
# {'requests': '2.31.0'}

metadata = generate_script_metadata(deps)
print(metadata)
# /// script
# requires-python = ">=3.12"
# dependencies = [
#     "requests==2.31.0",
# ]
# ///
```

## Development

This project uses `uv` for management.

```bash
# Install dependencies
uv sync

# Run tests
uv run pytest
```
