# Publishing crawlgate to PyPI

## Prerequisites

1. PyPI account at https://pypi.org
2. Installed build tools

```bash
pip install build twine
```

## First Time Setup

### 1. Create PyPI Account

1. Go to https://pypi.org/account/register/
2. Verify email
3. Enable 2FA (recommended)

### 2. Create API Token

1. Go to https://pypi.org/manage/account/
2. Scroll to "API tokens"
3. Click "Add API token"
4. Name: "crawlgate-upload"
5. Scope: "Entire account" (or project-specific after first upload)
6. Copy the token (starts with `pypi-`)

### 3. Configure ~/.pypirc

```ini
[pypi]
username = __token__
password = pypi-your-token-here
```

Or use environment variable:
```bash
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-your-token-here
```

## Publishing

### 1. Update Version

Edit `pyproject.toml`:
```toml
[project]
version = "1.0.1"  # Update version
```

### 2. Build Package

```bash
cd sdk-python
rm -rf dist/
python -m build
```

This creates:
- `dist/crawlgate-1.0.0.tar.gz` (source)
- `dist/crawlgate-1.0.0-py3-none-any.whl` (wheel)

### 3. Test on TestPyPI (Optional)

```bash
twine upload --repository testpypi dist/*
```

Test installation:
```bash
pip install --index-url https://test.pypi.org/simple/ crawlgate
```

### 4. Publish to PyPI

```bash
twine upload dist/*
```

### 5. Verify

```bash
pip install crawlgate
python -c "from crawlgate import CrawlGateClient; print('OK')"
```

Or visit: https://pypi.org/project/crawlgate/

## Version Management

Follow semantic versioning:
- **Patch** (1.0.0 → 1.0.1): Bug fixes
- **Minor** (1.0.0 → 1.1.0): New features, backward compatible
- **Major** (1.0.0 → 2.0.0): Breaking changes

## CI/CD Publishing (GitHub Actions)

Create `.github/workflows/publish-python.yml`:

```yaml
name: Publish Python SDK to PyPI

on:
  release:
    types: [created]

jobs:
  publish:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - uses: actions/setup-python@v5
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: pip install build twine

      - name: Build
        working-directory: ./sdk-python
        run: python -m build

      - name: Publish
        working-directory: ./sdk-python
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
        run: twine upload dist/*
```

Add `PYPI_TOKEN` to GitHub repository secrets.

## Troubleshooting

### "Package name already exists"
The name `crawlgate` must be unique on PyPI.

### "Invalid credentials"
```bash
# Check token format
echo $TWINE_PASSWORD | head -c 10
# Should start with: pypi-

# Re-configure
rm ~/.pypirc
```

### "File already exists"
You cannot overwrite an existing version. Bump the version number.

### Build errors
```bash
rm -rf dist/ build/ *.egg-info/
pip install --upgrade build twine
python -m build
```

## Local Development Install

```bash
cd sdk-python
pip install -e .
```

This installs in "editable" mode - changes to source files are reflected immediately.
