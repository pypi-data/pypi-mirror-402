# PyPI Publication Guide for RFP Kit CLI

This guide walks you through publishing RFP Kit CLI to PyPI so users can install it with `pip install rfpkit-cli`.

## Prerequisites

1. **PyPI Account**: Create accounts on both [PyPI](https://pypi.org/account/register/) and [TestPyPI](https://test.pypi.org/account/register/)
2. **API Tokens**: Generate API tokens for both PyPI and TestPyPI
3. **Git Repository**: Ensure your code is committed and pushed to GitHub

## Manual Publication Process

### 1. Prepare Release

Update version numbers and create a git tag:

```bash
# Update version in src/rfpkit_cli/__init__.py
# Update version in pyproject.toml
# Commit changes
git add .
git commit -m "Prepare release v0.1.1"
git tag v0.1.1
git push origin main
git push origin v0.1.1
```

### 2. Build and Test Locally

```bash
# Run the build script
./scripts/build-pypi.sh

# Test the built package
pip install dist/rfpkit_cli-*.whl
rfpkit --help
```

### 3. Publish to TestPyPI (Optional but Recommended)

```bash
# Upload to TestPyPI first to test
python -m twine upload --repository testpypi dist/*
# You'll be prompted for username (__token__) and password (your TestPyPI API token)

# Test installation from TestPyPI
pip install --index-url https://test.pypi.org/simple/ rfpkit-cli
```

### 4. Publish to PyPI

```bash
# Upload to PyPI
python -m twine upload dist/*
# You'll be prompted for username (__token__) and password (your PyPI API token)
```

### 5. Verify Publication

```bash
# Test installation from PyPI
pip install rfpkit-cli
rfpkit --help
```

## Automated Publication with GitHub Actions

The repository includes automated workflows that will publish to PyPI when you create a release:

### Setup PyPI Trusted Publishing (Recommended)

1. Go to [PyPI Trusted Publishers](https://pypi.org/manage/account/publishing/)
2. Add a new trusted publisher with these settings:
   - **PyPI Project Name**: `rfpkit-cli`
   - **Owner**: `sketabchi`
   - **Repository name**: `rfpkit`
   - **Workflow filename**: `publish-pypi.yml`
   - **Environment name**: `pypi`

### Create GitHub Release

1. Go to your GitHub repository
2. Click "Releases" → "Create a new release"
3. Create a tag (e.g., `v0.1.1`)
4. Fill in release title and description
5. Click "Publish release"

The GitHub Action will automatically:
- Build the package
- Run tests
- Publish to PyPI using trusted publishing

## Environment Configuration

### For Manual Publishing

Configure your PyPI credentials:

```bash
# Create ~/.pypirc file
[distutils]
index-servers = 
  pypi
  testpypi

[pypi]
  username = __token__
  password = pypi-your-api-token-here

[testpypi]
  repository = https://test.pypi.org/legacy/
  username = __token__
  password = pypi-your-testpypi-api-token-here
```

### For GitHub Actions

The workflows are configured to use PyPI Trusted Publishing, which is more secure than API tokens.

## Version Management

Update versions in both places when releasing:

1. **`src/rfpkit_cli/__init__.py`**:
   ```python
   __version__ = "0.1.1"
   ```

2. **`pyproject.toml`**:
   ```toml
   version = "0.1.1"
   ```

## Troubleshooting

### Build Issues
- Ensure all dependencies are installed
- Check that package structure is correct
- Verify `__init__.py` exists and contains `__version__`

### Upload Issues
- Verify API token is correct
- Check that version number hasn't been used before
- Ensure package name is available on PyPI

### Filename Already Exists Error
If you get "Filename or contents already exists" error:

1. **Change the version number** in both files:
   - `src/rfpkit_cli/__init__.py`: Update `__version__ = "x.x.x"`
   - `pyproject.toml`: Update `version = "x.x.x"`

2. **Rebuild and upload**:
   ```bash
   ./scripts/build-pypi.sh
   python -m twine upload dist/*
   ```

PyPI never allows reusing filenames, even if the old file was deleted. Each version must be unique.

### Installation Issues
- Check that all dependencies are correctly specified
- Verify entry point configuration
- Test in clean environment

## Post-Publication

After successful publication:

1. Update README with PyPI installation instructions
2. Test installation from PyPI: `pip install rfpkit-cli`
3. Update project documentation
4. Announce the release

## Package Information

- **Package Name**: `rfpkit-cli`
- **PyPI URL**: https://pypi.org/project/rfpkit-cli/
- **Command**: `rfpkit`
- **Entry Point**: `rfpkit_cli:main`

## Resources

- [Python Packaging Guide](https://packaging.python.org/)
- [PyPI Trusted Publishers](https://docs.pypi.org/trusted-publishers/)
- [Twine Documentation](https://twine.readthedocs.io/)