# Publishing surfadev to PyPI

This guide covers how to publish the `surfadev` package to PyPI.

## Prerequisites

1. **PyPI Account**
   - Create an account at https://pypi.org/account/register/
   - Create an account at https://test.pypi.org/account/register/ (for testing)

2. **API Tokens**
   - Go to https://pypi.org/manage/account/token/ and create an API token
   - Go to https://test.pypi.org/manage/account/token/ and create an API token
   - Save these tokens securely

3. **Required Tools**
   ```bash
   pip install build twine
   ```

## Step 1: Prepare the Package

1. **Update version in `pyproject.toml`**:
   ```toml
   version = "0.2.0"  # Update this for each release
   ```

2. **Update CHANGELOG** (optional but recommended):
   - Document changes in each version
   - Keep a changelog file if you have one

3. **Verify metadata**:
   - Check author information
   - Verify license
   - Review description and keywords
   - Ensure all URLs are correct

## Step 2: Build Distributions

Build both source distribution (sdist) and wheel:

```bash
cd analytics-sdk
python -m build
```

This creates:
- `dist/surfadev-0.2.0.tar.gz` (source distribution)
- `dist/surfadev-0.2.0-py3-none-any.whl` (wheel)

## Step 3: Test Locally (Optional)

Test the installation locally:

```bash
# Install from wheel
pip install dist/surfadev-0.2.0-py3-none-any.whl

# Or install from source
pip install dist/surfadev-0.2.0.tar.gz

# Test import
python -c "from surfadev import AnalyticsClient; print('✅ Import successful')"

# Uninstall when done testing
pip uninstall surfadev -y
```

## Step 4: Check Distribution (Recommended)

Check the distribution for common issues:

```bash
twine check dist/*
```

This will:
- Verify README format
- Check for common metadata issues
- Validate package structure

## Step 5: Upload to Test PyPI (Recommended)

**Always test on Test PyPI first!**

```bash
twine upload --repository testpypi dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your Test PyPI API token (starts with `pypi-`)

**Test installation from Test PyPI:**

```bash
pip install --index-url https://test.pypi.org/simple/ surfadev
```

## Step 6: Upload to Production PyPI

Once tested, upload to production PyPI:

```bash
twine upload dist/*
```

You'll be prompted for:
- Username: `__token__`
- Password: Your PyPI API token (starts with `pypi-`)

## Step 7: Verify Publication

1. **Check PyPI page**:
   - Visit: https://pypi.org/project/surfadev/
   - Verify all metadata is displayed correctly
   - Check README renders properly

2. **Test installation**:
   ```bash
   pip install surfadev
   python -c "from surfadev import AnalyticsClient; print('✅ Installed successfully')"
   ```

## Automation (Optional)

### Using `.pypirc` File

Create `~/.pypirc` (or `%USERPROFILE%\.pypirc` on Windows):

```ini
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YourProductionTokenHere

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YourTestTokenHere
```

Then upload with:
```bash
twine upload --repository testpypi dist/*  # Test
twine upload --repository pypi dist/*      # Production
```

### Using Environment Variables

```bash
# Test PyPI
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-YourTestTokenHere
twine upload --repository testpypi dist/*

# Production PyPI
export TWINE_USERNAME=__token__
export TWINE_PASSWORD=pypi-YourProductionTokenHere
twine upload dist/*
```

## Version Bumping

For future releases:

1. **Update version in `pyproject.toml`**:
   ```toml
   version = "0.2.1"  # Patch release
   # or
   version = "0.3.0"  # Minor release
   # or
   version = "1.0.0"  # Major release
   ```

2. **Follow semantic versioning**:
   - **MAJOR** (1.0.0): Breaking changes
   - **MINOR** (0.1.0): New features, backwards compatible
   - **PATCH** (0.0.1): Bug fixes, backwards compatible

3. **Rebuild and upload**:
   ```bash
   python -m build
   twine check dist/*
   twine upload --repository testpypi dist/*  # Test first
   twine upload dist/*  # Production
   ```

## Troubleshooting

### "Package already exists"
- Version number already published
- Solution: Increment version in `pyproject.toml`

### "Invalid password"
- Check your API token is correct
- Ensure you're using `__token__` as username
- Token should start with `pypi-`

### "README doesn't render"
- Check README is valid Markdown
- Run `twine check dist/*` to validate
- Ensure `readme = "README.md"` is set in `pyproject.toml`

### "Package not found after upload"
- PyPI CDN takes a few minutes to update
- Wait 2-5 minutes and try again
- Check https://pypi.org/project/surfadev/

## Security Best Practices

1. **Never commit API tokens** to version control
2. **Use API tokens** instead of passwords
3. **Use Test PyPI** first to catch issues
4. **Review package contents** before uploading
5. **Use `.pypirc` file** with proper permissions (600 on Unix)

## Additional Resources

- [PyPI Documentation](https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Python Packaging User Guide](https://packaging.python.org/)
- [Semantic Versioning](https://semver.org/)
