# PyPI Publication Guide

Complete guide for publishing MusicList for Soundiiz to PyPI.

## 📋 Table of Contents

- [Prerequisites](#prerequisites)
- [One-Time Setup](#one-time-setup)
- [Manual Publishing](#manual-publishing)
- [Automated Publishing with GitHub Actions](#automated-publishing-with-github-actions)
- [Version Management](#version-management)
- [Troubleshooting](#troubleshooting)

---

## Prerequisites

### 1. PyPI Account

Create accounts on:
- **PyPI** (production): https://pypi.org/account/register/
- **TestPyPI** (testing): https://test.pypi.org/account/register/

### 2. Install Build Tools

```bash
pip install --upgrade build twine
```

### 3. API Tokens

#### Create PyPI API Token:
1. Go to https://pypi.org/manage/account/token/
2. Click "Add API token"
3. Name: `musiclist-for-soundiiz-publish`
4. Scope: Project: `musiclist-for-soundiiz` (or "Entire account" for first publish)
5. Copy the token (starts with `pypi-`)

#### Create TestPyPI API Token:
1. Go to https://test.pypi.org/manage/account/token/
2. Same steps as above
3. Copy the token

---

## One-Time Setup

### Configure `.pypirc` (Optional but Recommended)

```bash
# Create config file
cat > ~/.pypirc << 'EOF'
[distutils]
index-servers =
    pypi
    testpypi

[pypi]
username = __token__
password = pypi-YOUR-TOKEN-HERE

[testpypi]
repository = https://test.pypi.org/legacy/
username = __token__
password = pypi-YOUR-TESTPYPI-TOKEN-HERE
EOF

# Secure the file
chmod 600 ~/.pypirc
```

**⚠️ IMPORTANT**: Never commit `.pypirc` to git!

---

## Manual Publishing

### Step 1: Update Version

Update version in **3 places**:

1. **setup.py**:
```python
version="1.0.5",
```

2. **pyproject.toml**:
```toml
version = "1.0.5"
```

3. **src/musiclist_for_soundiiz/__init__.py**:
```python
__version__ = "1.0.5"
```

### Step 2: Clean Previous Builds

```bash
# Remove old builds
rm -rf build/ dist/ *.egg-info src/*.egg-info

# Clean Python cache
find . -type d -name __pycache__ -exec rm -rf {} +
find . -type f -name "*.pyc" -delete
```

### Step 3: Build Package

```bash
# Build source distribution and wheel
python -m build

# Check generated files
ls -lh dist/
# Should show:
# musiclist_for_soundiiz-1.0.5-py3-none-any.whl
# musiclist_for_soundiiz-1.0.5.tar.gz
```

### Step 4: Test on TestPyPI (Recommended)

```bash
# Upload to TestPyPI
python -m twine upload --repository testpypi dist/*

# Test installation
pip install --index-url https://test.pypi.org/simple/ musiclist-for-soundiiz

# Test the package
musiclist-for-soundiiz --version
musiclist-for-soundiiz --help

# Uninstall test version
pip uninstall musiclist-for-soundiiz -y
```

### Step 5: Publish to PyPI

```bash
# Upload to PyPI
python -m twine upload dist/*

# Or if you have .pypirc configured:
twine upload dist/*

# Verify on PyPI
# Visit: https://pypi.org/project/musiclist-for-soundiiz/
```

### Step 6: Test Real Installation

```bash
# Install from PyPI
pip install musiclist-for-soundiiz

# Test CLI
musiclist-for-soundiiz --version

# Test GUI
musiclist-for-soundiiz-gui

# Uninstall
pip uninstall musiclist-for-soundiiz
```

### Step 7: Create Git Tag

```bash
# Create version tag
git tag -a v1.0.5 -m "Release version 1.0.5"

# Push tags
git push origin v1.0.5

# Or push all tags
git push --tags
```

---

## Automated Publishing with GitHub Actions

The repository includes a GitHub Actions workflow for automatic PyPI publishing.

### Setup GitHub Secrets

1. Go to your repository on GitHub
2. Settings → Secrets and variables → Actions
3. Add repository secrets:
   - `PYPI_API_TOKEN`: Your PyPI API token
   - `TEST_PYPI_API_TOKEN`: Your TestPyPI API token (optional)

### Workflow Configuration

The workflow (`.github/workflows/publish-to-pypi.yml`) automatically:
- Triggers on new version tags (e.g., `v1.0.5`)
- Runs tests
- Builds the package
- Publishes to TestPyPI (optional)
- Publishes to PyPI

### Trigger Automated Publishing

```bash
# Update version in files (setup.py, pyproject.toml, __init__.py)
# Commit changes
git add setup.py pyproject.toml src/musiclist_for_soundiiz/__init__.py
git commit -m "Bump version to 1.0.5"
git push

# Create and push tag
git tag -a v1.0.5 -m "Release version 1.0.5"
git push origin v1.0.5

# GitHub Actions will automatically publish to PyPI
```

### Monitor Workflow

1. Go to GitHub → Actions tab
2. Watch the "Publish to PyPI" workflow
3. Check for success ✅ or errors ❌

---

## Version Management

### Semantic Versioning

Follow [SemVer](https://semver.org/): `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes (e.g., `2.0.0`)
- **MINOR**: New features, backward-compatible (e.g., `1.1.0`)
- **PATCH**: Bug fixes, backward-compatible (e.g., `1.0.1`)

### Version Checklist

Before releasing:

- [ ] Update version in `setup.py`
- [ ] Update version in `pyproject.toml`
- [ ] Update version in `src/musiclist_for_soundiiz/__init__.py`
- [ ] Update `CHANGELOG.md` (if exists)
- [ ] Run tests: `pytest`
- [ ] Check code quality: `black`, `flake8`, `mypy`
- [ ] Build locally: `python -m build`
- [ ] Test installation locally
- [ ] Commit version changes
- [ ] Create git tag
- [ ] Push to GitHub

---

## Troubleshooting

### Error: "File already exists"

**Problem**: Version already published to PyPI

**Solution**: 
- You **cannot** re-upload the same version
- Increment version number
- PyPI versions are immutable

```bash
# Fix: Bump version
# In setup.py: version="1.0.6"
# In pyproject.toml: version = "1.0.6"
# Rebuild and re-upload
```

### Error: "Invalid username/password"

**Problem**: Wrong credentials

**Solution**:
```bash
# Use API token, not password
# Username should be: __token__
# Password should be: pypi-...

# Re-upload with explicit token
twine upload --username __token__ --password pypi-YOUR-TOKEN-HERE dist/*
```

### Error: "Permission denied"

**Problem**: Token doesn't have permission for this project

**Solution**:
1. Create new token with "Entire account" scope
2. Or add specific project permission after first upload

### Error: "Invalid distribution"

**Problem**: Build files corrupted or missing

**Solution**:
```bash
# Clean and rebuild
rm -rf build/ dist/ *.egg-info
python -m build
twine check dist/*
```

### Verify Package Contents

```bash
# Check what's included in package
tar -tzf dist/musiclist_for_soundiiz-1.0.5.tar.gz

# Or for wheel
unzip -l dist/musiclist_for_soundiiz-1.0.5-py3-none-any.whl
```

### Test Before Publishing

```bash
# Validate package
twine check dist/*

# Test installation locally
pip install dist/musiclist_for_soundiiz-1.0.5-py3-none-any.whl

# Test commands
musiclist-for-soundiiz --version
```

---

## PyPI Best Practices

### 1. Use TestPyPI First

Always test on TestPyPI before publishing to production:

```bash
# Upload to TestPyPI
twine upload --repository testpypi dist/*

# Test install
pip install --index-url https://test.pypi.org/simple/ musiclist-for-soundiiz
```

### 2. Validate Before Upload

```bash
# Check package
twine check dist/*

# Should show: PASSED
```

### 3. Keep Credentials Secure

- ❌ Never commit API tokens
- ✅ Use environment variables
- ✅ Use GitHub Secrets for CI/CD
- ✅ Set restrictive permissions on `.pypirc`

### 4. Document Changes

Create `CHANGELOG.md`:

```markdown
# Changelog

## [1.0.5] - 2026-01-18
### Added
- PyPI publication support
- Comprehensive documentation

### Fixed
- Unicode handling in Windows builds

## [1.0.0] - 2025-XX-XX
### Added
- Initial release
```

---

## Quick Reference

### Publish Checklist

```bash
# 1. Update version (3 files)
# 2. Clean
rm -rf build/ dist/ *.egg-info

# 3. Build
python -m build

# 4. Check
twine check dist/*

# 5. Test (optional)
twine upload --repository testpypi dist/*

# 6. Publish
twine upload dist/*

# 7. Tag
git tag -a v1.0.5 -m "Release 1.0.5"
git push --tags
```

### Useful Commands

```bash
# Check installed version
pip show musiclist-for-soundiiz

# List all versions on PyPI
pip index versions musiclist-for-soundiiz

# Install specific version
pip install musiclist-for-soundiiz==1.0.5

# Install from GitHub (development)
pip install git+https://github.com/lucmuss/musiclist-for-soundiiz.git
```

---

## Resources

- **PyPI**: https://pypi.org/project/musiclist-for-soundiiz/
- **TestPyPI**: https://test.pypi.org/project/musiclist-for-soundiiz/
- **Packaging Guide**: https://packaging.python.org/
- **Twine Docs**: https://twine.readthedocs.io/
- **GitHub Actions**: https://docs.github.com/en/actions

---

**🎉 Congratulations! Your package is now on PyPI and anyone can install it with `pip install musiclist-for-soundiiz`!**
