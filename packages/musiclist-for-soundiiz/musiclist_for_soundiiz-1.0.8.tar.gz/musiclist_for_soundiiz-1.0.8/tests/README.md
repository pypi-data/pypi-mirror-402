# Test Documentation

This test suite ensures that MusicList for Soundiiz functions correctly.

## Test Structure

```
tests/
├── __init__.py
├── README.md                    # This file
├── test_extractor.py           # Unit tests for metadata extraction
├── test_exporter.py            # Unit tests for export functions
├── test_integration.py         # Integration tests with real audio files
└── fixtures/                   # Test fixtures
    └── music/                  # Nested directory structure
        ├── Rock/
        │   ├── test_file.mp3
        │   └── test_file.flac
        ├── Pop/
        │   └── test_file.aac
        └── Electronic/
            ├── test_file.wma
            └── Techno/
                └── test_file.ogg
```

## Test Categories

### 1. Unit Tests (test_extractor.py)

**Tests:** Metadata extraction and file scanning

- ✅ Support for all audio formats (AAC, AU, FLAC, MP3, OGG, M4A, WAV, WMA)
- ✅ Recursive/non-recursive scanning
- ✅ Filename parsing ("Artist - Title" format)
- ✅ Error handling for invalid files
- ✅ Case-insensitive file extensions
- ✅ Filtering by extensions

**46 Tests** - Covers all edge cases

### 2. Unit Tests (test_exporter.py)

**Tests:** Export to different formats

- ✅ CSV export (Soundiiz-compatible)
  - With special characters (commas, quotes)
  - Automatic splitting for large playlists
  - Correct header formatting
- ✅ JSON export (pretty & compact)
- ✅ M3U export (extended & simple)
- ✅ TXT export
- ✅ Unicode support

**24 Tests** - Validates all export formats

### 3. Integration Tests (test_integration.py)

**Tests:** End-to-end workflows with real audio files

#### TestRealAudioFiles (5 Tests)
Validates metadata extraction from real audio files:

```python
# Example: MP3 metadata test
metadata = extractor.extract_metadata("test_file.mp3")
assert metadata["title"] == "Loneliness"
assert metadata["artist"] == "Tomcraft"
assert metadata["album"] == "Loneliness"
```

**Tested formats:**
- MP3 (Rock/test_file.mp3)
- FLAC (Rock/test_file.flac)
- AAC (Pop/test_file.aac)
- OGG (Electronic/Techno/test_file.ogg)
- WMA (Electronic/test_file.wma)

#### TestNestedDirectoryStructure (5 Tests)
Tests nested directory structures:

- ✅ Recursive scanning finds all files in subdirectories
- ✅ Non-recursive scanning only top-level
- ✅ Metadata extraction from nested structures
- ✅ Filtering by extension in nested folders
- ✅ Multiple formats in same directory

#### TestEndToEndWorkflow (3 Tests)
Complete workflows:

1. **CSV Export Workflow**
   - Scan → Extract → Export to CSV
   - Validate Soundiiz format
   
2. **JSON Export Workflow**
   - Scan → Extract → Export to JSON
   - Validate JSON structure

3. **Metadata Consistency**
   - Same song in different formats
   - Consistent metadata across formats

## Test Fixtures

### Directory Structure

The test fixtures simulate a real music library:

```
fixtures/music/
├── Rock/              # Genre folder with multiple formats
│   ├── test_file.mp3  # Loneliness - Tomcraft
│   └── test_file.flac # Loneliness - Tomcraft
├── Pop/               # Different genre
│   └── test_file.aac  # Loneliness - Tomcraft
└── Electronic/        # Nested genre
    ├── test_file.wma
    └── Techno/        # Sub-genre
        └── test_file.ogg # Loneliness - Tomcraft
```

### Real Audio Files

All test files are **real audio files** with embedded metadata:

| File | Format | Title | Artist | Album |
|------|--------|-------|--------|-------|
| test_file.mp3 | MP3 | Loneliness | Tomcraft | Loneliness |
| test_file.flac | FLAC | Loneliness | Tomcraft | Loneliness |
| test_file.aac | AAC | Loneliness | Tomcraft | Loneliness |
| test_file.ogg | OGG Vorbis | Loneliness | Tomcraft | Loneliness |
| test_file.wma | WMA | test_file | Unknown Artist | Unknown Album |

## Running Tests

### All Tests

```bash
pytest
```

### With Coverage

```bash
pytest --cov=musiclist_for_soundiiz --cov-report=html
```

### Only Unit Tests

```bash
pytest tests/test_extractor.py tests/test_exporter.py
```

### Only Integration Tests

```bash
pytest tests/test_integration.py
```

### Single Test Class

```bash
pytest tests/test_integration.py::TestRealAudioFiles
```

### Single Test

```bash
pytest tests/test_integration.py::TestRealAudioFiles::test_extract_mp3_metadata -v
```

### With Verbose Output

```bash
pytest -v
```

## Test Coverage

Current: **77% Code Coverage**

- `__init__.py`: 100%
- `exporter.py`: 99%
- `extractor.py`: 95%
- `cli.py`: 18% (CLI is mainly tested manually)

## Adding New Tests

### Unit Test Example

```python
def test_new_feature(self):
    """Test description."""
    # Arrange
    extractor = MusicFileExtractor()
    
    # Act
    result = extractor.some_method()
    
    # Assert
    assert result == expected_value
```

### Integration Test with Fixtures

```python
def test_with_real_file(self, fixtures_dir):
    """Test with real audio file."""
    audio_file = fixtures_dir / "Rock" / "test_file.mp3"
    
    if not audio_file.exists():
        pytest.skip(f"File not found: {audio_file}")
    
    extractor = MusicFileExtractor()
    metadata = extractor.extract_metadata(audio_file)
    
    assert metadata["title"] == "Loneliness"
```

## Continuous Integration

Tests are run automatically on every push/pull request:

- **GitHub Actions** (`.github/workflows/ci.yml`)
- **Multi-Platform**: Linux, Windows, macOS
- **Multi-Python**: 3.8, 3.9, 3.10, 3.11, 3.12

## Best Practices

1. **Keep each test isolated** - No dependencies between tests
2. **Use fixtures** - For reusable test data
3. **Clear assertions** - What is being tested and why
4. **Test edge cases** - Empty directories, corrupted files, etc.
5. **Use real data** - Integration tests with real audio files

## Debugging

### Test Fails

```bash
# Run single test with verbose output
pytest tests/test_integration.py::test_name -vv

# With debugger
pytest --pdb tests/test_integration.py::test_name
```

### Fixtures Not Found

```bash
# Check if fixtures exist
ls -la tests/fixtures/music/Rock/
```

### Import Errors

```bash
# Make sure package is installed
pip install -e .
```

## Statistics

- **Total**: 59 Tests
- **Unit Tests**: 46
- **Integration Tests**: 13
- **Test Runtime**: ~0.3s
- **Coverage**: 77%
- **Status**: ✅ All tests passing
