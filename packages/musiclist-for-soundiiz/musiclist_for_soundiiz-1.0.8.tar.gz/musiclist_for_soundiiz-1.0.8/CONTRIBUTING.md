# Contributing to MusicList for Soundiiz

Thank you for your interest in contributing to this project! 🎵

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [How Can I Contribute?](#how-can-i-contribute)
- [Development Setup](#development-setup)
- [Development Process](#development-process)
- [Writing Tests](#writing-tests)
- [Code Style](#code-style)
- [Pull Request Process](#pull-request-process)
- [Issue Guidelines](#issue-guidelines)

## Code of Conduct

This project follows a Code of Conduct. By participating, you are expected to uphold this code. Please report unacceptable behavior.

## How Can I Contribute?

### 🐛 Reporting Bugs

If you find a bug:

1. Check if the bug is already reported in [Issues](https://github.com/lucmuss/musiclist-for-soundiiz/issues)
2. If not, create a new issue with:
   - Descriptive title
   - Steps to reproduce
   - Expected vs. actual behavior
   - Your environment (OS, Python version)
   - Relevant log output

### 💡 Suggesting Features

Feature suggestions are welcome! Please:

1. Check existing feature requests
2. Create an issue with:
   - Clear description of the feature
   - Use cases
   - Possible implementation

### 🔧 Contributing Code

1. Fork the repository
2. Create a feature branch
3. Implement your changes
4. Write tests
5. Ensure all tests pass
6. Create a Pull Request

## Development Setup

### Prerequisites

- Python 3.8+
- Git

### Setup

```bash
# Fork and clone the repository
git clone https://github.com/YOUR-USERNAME/musiclist-for-soundiiz.git
cd musiclist-for-soundiiz

# Create virtual environment
python3 -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install development dependencies
pip install -e ".[dev]"
```

## Development Process

### Branch Naming Conventions

- `feature/` - New features (e.g., `feature/add-spotify-export`)
- `bugfix/` - Bug fixes (e.g., `bugfix/fix-unicode-issue`)
- `docs/` - Documentation updates (e.g., `docs/improve-readme`)
- `test/` - Test improvements (e.g., `test/add-integration-tests`)

### Commit Messages

We follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>: <description>

[optional body]

[optional footer]
```

**Types:**
- `feat:` - New feature
- `fix:` - Bug fix
- `docs:` - Documentation
- `test:` - Tests
- `refactor:` - Code refactoring
- `style:` - Code style (formatting)
- `chore:` - Maintenance tasks

**Examples:**
```bash
feat: add support for Spotify playlists
fix: handle unicode characters in filenames
docs: update installation instructions
test: add tests for OGG format
```

## Writing Tests

### Test Structure

```python
def test_descriptive_name(self):
    """Clear description of what is being tested."""
    # Arrange
    extractor = MusicFileExtractor()
    
    # Act
    result = extractor.find_music_files(test_dir)
    
    # Assert
    assert len(result) == expected_count
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov=musiclist_for_soundiiz --cov-report=html

# Single file
pytest tests/test_extractor.py

# Single test
pytest tests/test_extractor.py::TestMusicFileExtractor::test_find_music_files_mp3
```

### Test Coverage

- New features must be covered by tests
- Target: >90% code coverage
- Test edge cases and error handling

## Code Style

### Python Style Guide

We follow [PEP 8](https://www.python.org/dev/peps/pep-0008/) with some adjustments:

- Maximum line length: 100 characters
- Code formatting with `black`
- Import sorting with `isort`
- Use type hints

### Code Quality Tools

```bash
# Format code
black src tests

# Sort imports
isort src tests

# Linting
flake8 src tests --max-line-length=100

# Type checking
mypy src
```

### Pre-Commit

Recommended: Automatic code quality checks before commits:

```bash
pip install pre-commit
pre-commit install
```

## Pull Request Process

### Before Pull Request

✅ **Checklist:**

- [ ] Code follows project style
- [ ] All tests pass (`pytest`)
- [ ] New tests added for new features/fixes
- [ ] Documentation updated (if necessary)
- [ ] Code quality tools run
- [ ] Branch is up to date with main
- [ ] Commit messages follow conventions

### Creating Pull Request

1. **Title:** Clear, descriptive title
   ```
   feat: add support for WMA format
   ```

2. **Description:**
   ```markdown
   ## Changes
   - Added WMA file extension support
   - Added tests for WMA format
   - Updated documentation
   
   ## Motivation
   Users requested WMA support for Windows Media files
   
   ## Tests
   - Added unit tests for WMA file detection
   - All existing tests still pass
   
   Closes #42
   ```

3. **Review Process:**
   - At least one approval required
   - CI tests must pass
   - Address code review comments

## Issue Guidelines

### Bug Reports

```markdown
**Description:**
Brief summary of the problem

**Steps to Reproduce:**
1. Run `musiclist-for-soundiiz -i /path`
2. ...

**Expected Behavior:**
What should happen

**Actual Behavior:**
What actually happens

**Environment:**
- OS: Ubuntu 22.04
- Python: 3.10.5
- Version: 1.0.0

**Logs:**
```
ERROR output here
```
```

### Feature Requests

```markdown
**Feature Description:**
Clear description of the desired feature

**Use Case:**
Why is this feature useful?

**Proposed Implementation:**
(Optional) Ideas for implementation

**Alternatives:**
Other solutions you have considered
```

## Development Tips

### Debugging

```bash
# Verbose mode for detailed logs
musiclist-for-soundiiz -i /test -o output.csv -v

# Use Python debugger
python -m pdb -m musiclist_for_soundiiz.cli -i /test -o output.csv
```

### Creating Test Data

```python
# In tests: Create temporary test files
def test_example(tmp_path):
    test_file = tmp_path / "test.mp3"
    test_file.touch()
    # ...
```

### Useful Resources

- [Python Testing Best Practices](https://docs.python-guide.org/writing/tests/)
- [Mutagen Documentation](https://mutagen.readthedocs.io/)
- [pytest Documentation](https://docs.pytest.org/)

## Questions?

For questions:

- Create a [Discussion](https://github.com/lucmuss/musiclist-for-soundiiz/discussions)
- Ask in an existing issue
- Contact the maintainers

## License

By contributing, you agree that your contributions will be licensed under the MIT License.

---

**Thank you for your contributions! 🙏**
