# Publishing langgraph-viz to PyPI

This guide walks through building and publishing your updated package to PyPI with the new features (collapsible state properties and 100% completion fix).

## Prerequisites

Install required tools:
```bash
pip install --upgrade build twine
```

## Step 1: Update Version Number

Edit [`pyproject.toml`](file:///Users/mk/Desktop/workspace/ai-stuff/langgraph-viz/pyproject.toml) and bump the version:

```toml
[project]
name = "langgraph-viz"
version = "0.1.1"  # Changed from 0.1.0
```

**Version guidelines:**
- Bug fixes: `0.1.0` → `0.1.1` (patch)
- New features (backward compatible): `0.1.0` → `0.2.0` (minor)
- Breaking changes: `0.1.0` → `1.0.0` (major)

Since you're adding new features (collapsible state) and bug fixes (percentage), **`0.1.1`** or **`0.2.0`** would be appropriate.

## Step 2: Clean Old Builds

Remove old distribution files:
```bash
rm -rf dist/ build/ *.egg-info
```

## Step 3: Build the Package

The build script automatically:
1. Builds the frontend React app (`npm run build`)
2. Copies assets to `langgraph_viz/ui/`
3. Creates Python distribution files

Run the build script:
```bash
chmod +x build_package.sh
./build_package.sh
```

Or manually:
```bash
# Build frontend
cd frontend
npm install
npm run build
cd ..

# Build Python package
python3 -m build
```

This creates:
- `dist/langgraph_viz-0.1.1-py3-none-any.whl` (wheel)
- `dist/langgraph_viz-0.1.1.tar.gz` (source distribution)

## Step 4: Test Locally (Optional but Recommended)

Install the wheel locally to test:
```bash
# Create test environment
python3 -m venv test_env
source test_env/bin/activate

# Install from wheel
pip install dist/langgraph_viz-0.1.1-py3-none-any.whl

# Test it
python3 examples/chatbot_memory.py

# Verify in browser that:
# - Collapsible state properties work
# - Percentage reaches 100%

# Cleanup
deactivate
rm -rf test_env
```

## Step 5: Check Package Quality

Verify the package meets PyPI standards:
```bash
twine check dist/*
```

Expected output:
```
Checking dist/langgraph_viz-0.1.1-py3-none-any.whl: PASSED
Checking dist/langgraph_viz-0.1.1.tar.gz: PASSED
```

## Step 6: Upload to PyPI

### Option A: Test PyPI (Recommended First)

Test on TestPyPI before going to production:

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*
```

You'll be prompted for credentials:
- **Username**: Your TestPyPI username or `__token__`
- **Password**: Your TestPyPI password or API token

Test the installation:
```bash
pip install --index-url https://test.pypi.org/simple/ langgraph-viz==0.1.1
```

### Option B: Production PyPI

When ready for production:

```bash
# Upload to production PyPI
twine upload dist/*
```

You'll be prompted for credentials:
- **Username**: Your PyPI username or `__token__`
- **Password**: Your PyPI password or API token

## Step 7: Verify on PyPI

1. Visit https://pypi.org/project/langgraph-viz/
2. Check that version `0.1.1` is listed
3. Verify the description and metadata look correct

## Step 8: Test Installation

Install from PyPI to confirm:
```bash
pip install --upgrade langgraph-viz
python3 -c "import langgraph_viz; print(langgraph_viz.__version__)"
```

## Using API Tokens (Recommended)

Instead of passwords, use API tokens for better security.

### Create PyPI API Token:
1. Go to https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Name it (e.g., "langgraph-viz-uploads")
4. Scope it to the `langgraph-viz` project
5. Copy the token (starts with `pypi-`)

### Use token with twine:
```bash
# Set username to __token__
# Use the API token as password
twine upload dist/* -u __token__ -p pypi-AgEIcHlwaS5vcmc...
```

Or save in `~/.pypirc`:
```ini
[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...

[testpypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...
```

## Troubleshooting

### "File already exists" error
PyPI doesn't allow re-uploading the same version. You must bump the version number.

### Missing frontend assets
Ensure `npm run build` completed successfully and files exist in `langgraph_viz/ui/`.

### Import errors after install
The package structure might be wrong. Check `pyproject.toml`:
```toml
[tool.hatch.build.targets.wheel]
packages = ["langgraph_viz"]
artifacts = ["langgraph_viz/ui/**/*"]
```

### Version conflicts
Make sure version in `pyproject.toml` matches what you're uploading.

## Complete Workflow Summary

```bash
# 1. Update version in pyproject.toml (0.1.0 → 0.1.1)

# 2. Clean and build
rm -rf dist/ build/ *.egg-info
./build_package.sh

# 3. Check package
twine check dist/*

# 4. Upload to TestPyPI (optional)
twine upload --repository testpypi dist/*

# 5. Upload to PyPI
twine upload dist/*

# 6. Verify
pip install --upgrade langgraph-viz
```

## Changelog for v0.1.1

Document the changes in your README or CHANGELOG:

**New Features:**
- Collapsible state properties in State Viewer for better handling of long values
- Users can now expand/collapse nested objects/arrays interactively

**Bug Fixes:**
- Fixed percentage completion now correctly reaches 100% on the last event
- Previously maxed out at 90% due to 0-based indexing

**UI Improvements:**
- Cleaner state inspector with collapsed nested properties by default
- Better UX for workflows with long message arrays or deep state objects
