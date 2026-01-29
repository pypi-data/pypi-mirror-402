# Deploying Bah Lol to PyPI

This document explains how to deploy the Bah Lol framework to PyPI so others can install it using pip.

## Prerequisites

Before deploying, you need:

1. A PyPI account (register at https://pypi.org/account/register/)
2. `twine` installed: `pip install twine`
3. `build` installed: `pip install build`

## Steps to Deploy

### 1. Update Version Number (if needed)

Edit `pyproject.toml` and `setup.cfg` to increment the version number:

```toml
[project]
name = "bah-lol"
version = "1.0.1"  # Increment this for new releases
```

```ini
[metadata]
name = bah-lol
version = 1.0.1  # Increment this for new releases
```

### 2. Clean Previous Builds

Remove any previous build artifacts:

```bash
rm -rf dist/ build/ *.egg-info/
```

### 3. Build the Package

Create distribution files:

```bash
python -m build
```

This creates `dist/` directory with:
- `.tar.gz` file (source distribution)
- `.whl` file (wheel distribution)

### 4. Check the Package

Verify the package is correctly formatted:

```bash
twine check dist/*
```

### 5. Upload to Test PyPI (Optional but Recommended)

First, test the upload on Test PyPI:

```bash
twine upload --repository testpypi dist/*
```

Then test installation from Test PyPI:

```bash
pip install --index-url https://test.pypi.org/simple/ bah-lol
```

### 6. Upload to PyPI

Upload to the real PyPI:

```bash
twine upload dist/*
```

You'll need to provide your PyPI username and password/token.

## Using API Tokens (Recommended)

Instead of using your password, use an API token:

1. Go to https://pypi.org/manage/account/#api-tokens
2. Create a new API token
3. Use it with twine:

```bash
twine upload --username __token__ --password YOUR_API_TOKEN dist/*
```

## Post-Deployment Verification

After deployment, verify that the package can be installed:

```bash
pip install bah-lol
```

And test the basic functionality:

```python
from bah_lol import BahLol

app = BahLol()

@app.barang("/test")
def test_endpoint():
    return {"message": "Success!"}

# Note: Don't run app.gas() in a script that's being tested automatically
```

## Troubleshooting

### Common Issues:

1. **Package name already taken**: Choose a unique name
2. **Invalid metadata**: Check your `pyproject.toml` or `setup.cfg`
3. **Build errors**: Ensure all files referenced in setup exist

### Releasing Updates

For each release:
1. Update version numbers
2. Commit and tag the release: `git tag v1.0.1`
3. Follow the build/upload steps above

## GitHub Integration

Consider setting up GitHub Actions to automate releases:

1. Create `.github/workflows/release.yml`
2. Use `pypa/gh-action-pypi-publish` action
3. Store PyPI token as a GitHub secret

## Important Notes

- Once uploaded, package versions cannot be changed
- Choose version numbers carefully
- Test thoroughly before uploading
- Update documentation as needed