# Publishing to PyPI

This document describes how to build and publish yt-grabber to PyPI.

## Prerequisites

1. **PyPI Account**
   - Create an account at https://pypi.org/account/register/
   - Verify your email address

2. **API Token** (Recommended)
   - Go to https://pypi.org/manage/account/token/
   - Create a new API token with appropriate scope
   - Save the token securely (you'll only see it once)

3. **Install Publishing Tools**
   ```bash
   uv add --dev twine
   ```

## Building the Package

Build the distribution packages (wheel and source distribution):

```bash
uv build
```

This will create two files in the `dist/` directory:
- `yt_grabber-0.1.0-py3-none-any.whl` (wheel)
- `yt_grabber-0.1.0.tar.gz` (source distribution)

## Testing the Build

Before publishing, verify the package:

```bash
# Check the distribution
twine check dist/*

# Optionally, test install locally
pip install dist/yt_grabber-0.1.0-py3-none-any.whl
```

## Publishing to Test PyPI (Recommended First)

Test PyPI is a separate instance for testing package uploads:

```bash
# Upload to Test PyPI
uv publish --publish-url https://test.pypi.org/legacy/
```

Or with twine:

```bash
twine upload --repository testpypi dist/*
```

Test the installation:

```bash
pip install --index-url https://test.pypi.org/simple/ yt-grabber
```

## Publishing to PyPI

Once you've verified everything works on Test PyPI:

### Option 1: Using uv (Recommended)

```bash
uv publish
```

You'll be prompted for your PyPI credentials or API token.

### Option 2: Using twine

```bash
twine upload dist/*
```

Enter your PyPI credentials when prompted:
- Username: `__token__`
- Password: Your API token (including the `pypi-` prefix)

## Installing from PyPI

Once published, users can install with:

```bash
pip install yt-grabber
```

Or with uv:

```bash
uv pip install yt-grabber
```

## Version Updates

When releasing a new version:

1. **Update Version Number**
   - Edit `pyproject.toml` - update the `version` field
   - Edit `src/yt_grabber/__init__.py` - update `__version__`

2. **Update CHANGELOG.md**
   - Add a new section for the version
   - Document all changes (Added, Changed, Fixed, Removed)

3. **Commit Changes**
   ```bash
   git add pyproject.toml src/yt_grabber/__init__.py CHANGELOG.md
   git commit -m "chore: bump version to X.Y.Z"
   git tag vX.Y.Z
   git push origin main --tags
   ```

4. **Build and Publish**
   ```bash
   # Clean old builds
   rm -rf dist/

   # Build new distribution
   uv build

   # Publish to PyPI
   uv publish
   ```

## Troubleshooting

### Package Name Already Exists
If `yt-grabber` is taken, you'll need to:
1. Choose a different name in `pyproject.toml`
2. Update the package name throughout the documentation
3. Rebuild and publish with the new name

### Upload Fails
- Ensure you have the correct credentials
- Check that the version number hasn't been published before
- Verify your API token has the correct permissions

### Installation Issues
- Make sure Python version requirement (>=3.14) is clearly communicated
- Test on a clean virtual environment

## Security Best Practices

1. **Never commit API tokens** to version control
2. **Use API tokens** instead of passwords
3. **Scope tokens appropriately** (project-specific if possible)
4. **Rotate tokens periodically**
5. **Use 2FA** on your PyPI account

## Resources

- [Python Packaging User Guide](https://packaging.python.org/)
- [PyPI Help](https://pypi.org/help/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [uv Documentation](https://docs.astral.sh/uv/)
