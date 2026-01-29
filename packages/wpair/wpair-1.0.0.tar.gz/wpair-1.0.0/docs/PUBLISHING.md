# Publishing WPair to PyPI

This guide explains how to publish WPair to the Python Package Index (PyPI).

## Prerequisites

1. **PyPI Account**
   - Create account at https://pypi.org/account/register/
   - Create account at https://test.pypi.org/account/register/ (for testing)

2. **API Tokens** (Recommended over username/password)
   - Generate at https://pypi.org/manage/account/token/
   - Generate at https://test.pypi.org/manage/account/token/

3. **Install Build Tools**
   ```bash
   pip install build twine
   ```

## Pre-Publishing Checklist

Before publishing, ensure:

- [ ] All tests pass: `pytest tests/ -v`
- [ ] Version number updated in `pyproject.toml`
- [ ] `CHANGELOG.md` updated with release notes
- [ ] README.md is complete and accurate
- [ ] LICENSE file is present
- [ ] Git repository is clean (no uncommitted changes)
- [ ] Git tag created for version: `git tag v1.0.0`

## Build the Package

1. **Clean previous builds**
   ```bash
   rm -rf dist/ build/ *.egg-info
   ```

2. **Build source distribution and wheel**
   ```bash
   python -m build
   ```

3. **Verify build artifacts**
   ```bash
   ls -lh dist/
   # Should show:
   # wpair-1.0.0-py3-none-any.whl
   # wpair-1.0.0.tar.gz
   ```

4. **Check package contents**
   ```bash
   tar -tzf dist/wpair-1.0.0.tar.gz | less
   unzip -l dist/wpair-1.0.0-py3-none-any.whl | less
   ```

5. **Validate package metadata**
   ```bash
   twine check dist/*
   ```

## Test on TestPyPI (Highly Recommended)

TestPyPI is a separate instance of PyPI for testing packages before real publication.

1. **Upload to TestPyPI**
   ```bash
   twine upload --repository testpypi dist/*
   ```

   Or with API token:
   ```bash
   twine upload --repository testpypi dist/* \
     --username __token__ \
     --password pypi-AgEIcHl...  # Your TestPyPI token
   ```

2. **Test Installation**
   ```bash
   # Create test environment
   python -m venv test_env
   source test_env/bin/activate

   # Install from TestPyPI
   pip install --index-url https://test.pypi.org/simple/ \
     --extra-index-url https://pypi.org/simple/ \
     wpair

   # Test CLI
   wpair --version
   wpair --help
   wpair about

   # Deactivate
   deactivate
   rm -rf test_env
   ```

3. **Verify on TestPyPI**
   - Visit: https://test.pypi.org/project/wpair/
   - Check description renders correctly
   - Verify metadata (version, classifiers, links)

## Publish to PyPI

**⚠️ WARNING**: Once published to PyPI, you cannot delete or replace a version. Make sure everything is correct!

1. **Final verification**
   - Double-check version number
   - Ensure TestPyPI install worked correctly
   - Review package page on TestPyPI

2. **Upload to PyPI**
   ```bash
   twine upload dist/*
   ```

   Or with API token:
   ```bash
   twine upload dist/* \
     --username __token__ \
     --password pypi-AgEIcHl...  # Your PyPI token
   ```

3. **Verify Publication**
   - Visit: https://pypi.org/project/wpair/
   - Check all metadata
   - Verify README renders correctly

## Post-Publishing

1. **Test Installation from PyPI**
   ```bash
   # Create fresh environment
   python -m venv verify_env
   source verify_env/bin/activate

   # Install from PyPI
   pip install wpair

   # Test
   wpair --version
   wpair scan --help

   # Cleanup
   deactivate
   rm -rf verify_env
   ```

2. **Create GitHub Release**
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

   - Go to GitHub → Releases → Draft new release
   - Select tag v1.0.0
   - Title: "WPair v1.0.0"
   - Copy CHANGELOG.md content to description
   - Attach dist/wpair-1.0.0.tar.gz and dist/wpair-1.0.0-py3-none-any.whl
   - Publish release

3. **Update README Badges** (optional)
   ```markdown
   [![PyPI version](https://badge.fury.io/py/wpair.svg)](https://pypi.org/project/wpair/)
   [![Downloads](https://pepy.tech/badge/wpair)](https://pepy.tech/project/wpair)
   ```

4. **Announce Release**
   - Post on relevant security forums (with responsible disclosure context)
   - Tweet/social media (if applicable)
   - Update project website/documentation

## Version Management

WPair follows [Semantic Versioning](https://semver.org/):
- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
  - MAJOR: Breaking changes
  - MINOR: New features (backward compatible)
  - PATCH: Bug fixes

### Updating Version

1. Update version in `pyproject.toml`:
   ```toml
   version = "1.1.0"
   ```

2. Update CHANGELOG.md:
   ```markdown
   ## [1.1.0] - 2026-01-20
   ### Added
   - New feature X
   ```

3. Commit changes:
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "Bump version to 1.1.0"
   ```

4. Tag release:
   ```bash
   git tag v1.1.0
   git push origin main --tags
   ```

5. Rebuild and publish (see above steps)

## Troubleshooting

### "File already exists"
- You cannot re-upload the same version
- Increment version number and rebuild

### "Invalid distribution file"
- Run `twine check dist/*` for details
- Common issues: missing README, invalid metadata

### "Package name already taken"
- If "wpair" is taken, consider: wpair-cli, python-wpair, etc.
- Update `name` in pyproject.toml

### Dependencies not installing
- Ensure `dependencies` list in pyproject.toml is correct
- Test with fresh virtual environment

### README not rendering
- Ensure README.md is valid Markdown
- Check for problematic characters or HTML

## Security Considerations

### API Token Security

- **Never** commit API tokens to Git
- Store in environment variables:
  ```bash
  export TWINE_USERNAME=__token__
  export TWINE_PASSWORD=pypi-AgEIcHl...
  twine upload dist/*
  ```

- Or use `~/.pypirc`:
  ```ini
  [distutils]
  index-servers =
      pypi
      testpypi

  [pypi]
  username = __token__
  password = pypi-AgEIcHl...

  [testpypi]
  username = __token__
  password = pypi-AgEIcHl...
  ```

  **Important**: Set proper permissions: `chmod 600 ~/.pypirc`

### Package Security

- Sign releases with GPG (optional but recommended):
  ```bash
  twine upload --sign dist/*
  ```

- Enable 2FA on PyPI account

## Automation (Optional)

### GitHub Actions

Create `.github/workflows/publish.yml`:

```yaml
name: Publish to PyPI

on:
  release:
    types: [created]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          pip install build twine
      - name: Build package
        run: python -m build
      - name: Publish to PyPI
        env:
          TWINE_USERNAME: __token__
          TWINE_PASSWORD: ${{ secrets.PYPI_TOKEN }}
        run: twine upload dist/*
```

Add `PYPI_TOKEN` to GitHub repository secrets.

## References

- [Packaging Python Projects](https://packaging.python.org/tutorials/packaging-projects/)
- [PyPI Publishing Guide](https://packaging.python.org/guides/distributing-packages-using-setuptools/)
- [Twine Documentation](https://twine.readthedocs.io/)
- [Semantic Versioning](https://semver.org/)

---

For questions, see [CONTRIBUTING.md](../CONTRIBUTING.md) or open an issue.
