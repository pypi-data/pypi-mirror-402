# Build and Publish Guide for barie-facia-mcp

This guide explains how to build, test, and publish the `barie-facia-mcp` package to PyPI.

## Prerequisites

1. **Python 3.9+** installed
2. **Build tools** installed:
   ```bash
   pip install --upgrade build twine
   ```
3. **PyPI token** - You need a PyPI API token with upload permissions
4. **Package ownership** - You must own the package on PyPI or have upload permissions

## Project Structure

```
barie_facia_mcp/
├── facia_mcp/
│   ├── __init__.py      # Package initialization and version
│   ├── server.py        # MCP server implementation
│   └── client.py        # Facia API client
├── pyproject.toml        # Package configuration
├── README.md            # Package documentation
└── BUILD.md             # This file
```

## Building the Package

### 1. Clean Previous Builds

```bash
# Remove old build artifacts
rm -rf dist/ build/ *.egg-info
```

### 2. Update Version

Before building, update the version in two places:

**`pyproject.toml`:**
```toml
version = "0.1.1"  # Increment version number
```

**`facia_mcp/__init__.py`:**
```python
__version__ = "0.1.1"  # Must match pyproject.toml
```

### 3. Build Distributions

```bash
# Build both wheel and source distribution
python -m build

# Or build only wheel
python -m build --wheel

# Or build only source distribution
python -m build --sdist
```

This creates:
- `dist/barie_facia_mcp-<version>-py3-none-any.whl` (wheel)
- `dist/barie_facia_mcp-<version>.tar.gz` (source distribution)

### 4. Verify Build

```bash
# List built files
ls -lh dist/

# Check package contents (optional)
python -m zipfile -l dist/barie_facia_mcp-*.whl
```

## Testing Locally

### Test Installation

```bash
# Install from local build
pip install dist/barie_facia_mcp-*.whl

# Or install in editable mode for development
pip install -e .

# Test the command
barie-facia-mcp --help
```

### Test with uvx (Local)

```bash
# Test using uvx with local package
uvx --from ./dist/barie_facia_mcp-*.whl barie-facia-mcp --client-id "id" --client-secret "secret" --storage-dir "./images"
```

## Publishing to PyPI

### 1. Check Package

```bash
# Check package for common issues
python -m twine check dist/*
```

### 2. Upload to PyPI

**Using API Token (Recommended):**

```bash
python -m twine upload dist/* \
  --username __token__ \
  --password pypi-<your-token-here>
```

**Using Environment Variable:**

```bash
export TWINE_PASSWORD=pypi-<your-token-here>
python -m twine upload dist/* --username __token__
```

**Using .pypirc (Alternative):**

Create `~/.pypirc`:
```ini
[pypi]
username = __token__
password = pypi-<your-token-here>
```

Then upload:
```bash
python -m twine upload dist/*
```

### 3. Verify Upload

After publishing, verify on PyPI:
- https://pypi.org/project/barie-facia-mcp/

## Complete Build and Publish Workflow

Here's a complete script to build and publish:

```bash
#!/bin/bash

# 1. Clean
echo "Cleaning previous builds..."
rm -rf dist/ build/ *.egg-info

# 2. Update version (manual step - edit pyproject.toml and facia_mcp/__init__.py)
echo "Please update version in pyproject.toml and facia_mcp/__init__.py"
read -p "Press enter to continue after updating version..."

# 3. Build
echo "Building package..."
python -m build

# 4. Check
echo "Checking package..."
python -m twine check dist/*

# 5. Upload (uncomment when ready)
# echo "Uploading to PyPI..."
# python -m twine upload dist/* --username __token__ --password pypi-<your-token>

echo "Done! Package built successfully."
```

## Version Management

### Semantic Versioning

Follow [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Version Update Checklist

- [ ] Update `version` in `pyproject.toml`
- [ ] Update `__version__` in `facia_mcp/__init__.py`
- [ ] Update CHANGELOG.md (if you have one)
- [ ] Test locally
- [ ] Build package
- [ ] Check package
- [ ] Publish to PyPI

## Troubleshooting

### Error: "File already exists"

**Problem:** You're trying to upload a version that already exists on PyPI.

**Solution:** Increment the version number and rebuild.

```bash
# Update version in pyproject.toml and __init__.py
# Then rebuild and upload
rm -rf dist/ build/
python -m build
python -m twine upload dist/*
```

### Error: "Unable to determine which files to ship"

**Problem:** Hatchling can't find the package directory.

**Solution:** Ensure `pyproject.toml` has:
```toml
[tool.hatch.build.targets.wheel]
packages = ["facia_mcp"]
```

### Error: "Module not found" after installation

**Problem:** Package structure or imports are incorrect.

**Solution:**
1. Check that `facia_mcp/` directory exists
2. Verify `__init__.py` exists in `facia_mcp/`
3. Check imports use `facia_mcp.` prefix (not relative imports)

### Error: "Command not found: barie-facia-mcp"

**Problem:** Entry point not configured correctly.

**Solution:** Verify `pyproject.toml` has:
```toml
[project.scripts]
barie-facia-mcp = "facia_mcp.server:cli_main"
```

## Quick Reference

```bash
# Clean
rm -rf dist/ build/ *.egg-info

# Build
python -m build

# Check
python -m twine check dist/*

# Upload
python -m twine upload dist/* --username __token__ --password pypi-<token>

# Test install
pip install dist/barie_facia_mcp-*.whl

# Test with uvx
uvx barie-facia-mcp --client-id "id" --client-secret "secret" --storage-dir "./images"
```

## Environment Variables

You can set these to avoid typing the token each time:

```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-<your-token-here>
```

Then simply run:
```bash
python -m twine upload dist/*
```

## Security Notes

⚠️ **Never commit PyPI tokens to version control!**

- Use environment variables for tokens
- Add `.pypirc` to `.gitignore`
- Use `__token__` format for PyPI API tokens
- Rotate tokens if accidentally exposed

## Next Steps After Publishing

1. **Test installation:**
   ```bash
   uvx barie-facia-mcp --help
   ```

2. **Update documentation** if needed

3. **Announce release** (if applicable)

4. **Monitor PyPI** for any issues
