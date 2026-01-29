# Publishing to PyPI

This guide explains how to publish Sentinel-AI to PyPI.

## Prerequisites

1. Install build tools:
```bash
pip install build twine
```

2. Create accounts:
   - PyPI: https://pypi.org/account/register/
   - TestPyPI (optional, for testing): https://test.pypi.org/account/register/

## Build the Package

1. Ensure version is updated in `pyproject.toml`

2. Build the distribution:
```bash
python -m build
```

This creates:
- `dist/sentinel_ai-1.0.0-py3-none-any.whl`
- `dist/sentinel-ai-1.0.0.tar.gz`

## Test on TestPyPI (Optional but Recommended)

1. Upload to TestPyPI:
```bash
python -m twine upload --repository testpypi dist/*
```

2. Test installation:
```bash
pip install --index-url https://test.pypi.org/simple/ sentinel-ai
```

3. Test the package:
```bash
python -c "from sentinel_ai import configure_sentinel, sentinel_guard; print('Success!')"
```

## Publish to PyPI

1. Upload to PyPI:
```bash
python -m twine upload dist/*
```

2. Enter your PyPI credentials when prompted

3. Verify at: https://pypi.org/project/sentinel-ai/

## Install from PyPI

Users can now install with:
```bash
pip install sentinel-ai
```

## Version Updates

For new releases:

1. Update version in `pyproject.toml`:
```toml
version = "1.0.1"
```

2. Clean old builds:
```bash
rm -rf dist/ build/ *.egg-info
```

3. Rebuild and upload:
```bash
python -m build
python -m twine upload dist/*
```

## Using API Tokens (Recommended)

Instead of username/password, use API tokens:

1. Generate token at: https://pypi.org/manage/account/token/

2. Create `~/.pypirc`:
```ini
[pypi]
username = __token__
password = pypi-AgEIcHlwaS5vcmc...your-token-here
```

3. Upload:
```bash
python -m twine upload dist/*
```

## Automated Publishing with GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - uses: actions/setup-python@v4
      with:
        python-version: '3.x'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine
    - name: Build package
      run: python -m build
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

Add `PYPI_API_TOKEN` to GitHub repository secrets.

## Troubleshooting

### "File already exists"
- You cannot re-upload the same version
- Increment version number in `pyproject.toml`

### "Invalid distribution"
- Ensure `pyproject.toml` is properly formatted
- Check that all required files are included

### Import errors after installation
- Verify package structure matches `pyproject.toml`
- Check that `__init__.py` files exist in all packages

## Package Structure Checklist

```
sentinel-ai/
├── sentinel_ai/           # Main package
│   ├── __init__.py       # Package initialization
│   ├── core.py           # Core functionality
│   ├── redactor.py       # Data redaction
│   ├── policy.py         # Security policy
│   └── config/           # Configuration files
│       └── policy.yaml
├── examples/             # Example scripts
├── tests/                # Test suite (not included in distribution)
├── pyproject.toml        # Package metadata
├── README.md             # Documentation
├── LICENSE               # License file
└── .gitignore           # Git ignore rules
```

## Post-Publication

1. Verify installation:
```bash
pip install sentinel-ai
python -c "from sentinel_ai import sentinel_guard; print('✅ Package works!')"
```

2. Update documentation with installation instructions

3. Announce on relevant channels

4. Monitor PyPI stats: https://pypistats.org/packages/sentinel-ai
