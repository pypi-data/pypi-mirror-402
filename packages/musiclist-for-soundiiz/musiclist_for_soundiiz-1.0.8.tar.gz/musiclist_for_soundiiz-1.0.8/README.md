# MusicList for Soundiiz 🎵

[![CI](https://github.com/lucmuss/musiclist-for-soundiiz/workflows/CI/badge.svg)](https://github.com/lucmuss/musiclist-for-soundiiz/actions)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)

Professional command-line tool for extracting music file metadata for Soundiiz import.

## ✨ Features

- **🎵 Multi-Format Support** - AAC, AU, FLAC, MP3, OGG, M4A, WAV, WMA
- **📊 Multiple Export Formats** - CSV (Soundiiz), JSON, M3U, TXT
- **🔍 Intelligent Metadata Extraction** - Reads tags and parses filenames (format: "Artist - Title")
- **📁 Recursive Scanning** - Automatically searches all subdirectories
- **🔄 Automatic File Splitting** - Splits large playlists into multiple files (configurable)
- **🔎 Duplicate Detection** - Automatically finds and removes duplicate songs
- **📦 Batch Processing** - Process multiple directories simultaneously
- **🛡️ Robust Error Handling** - Skips problematic files and continues processing
- **✅ Production-Ready** - Fully tested with comprehensive test suite
- **🌐 Unicode Support** - Correct handling of special characters
- **📝 Detailed Logging** - Verbose mode for debugging

## 📋 Table of Contents

- [Installation](#installation)
- [Quick Start](#quick-start)
- [Usage Examples](#usage-examples)
- [Configuration](#configuration)
- [Export Formats](#export-formats)
- [Soundiiz Import](#soundiiz-import)
- [Development](#development)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## 🚀 Installation

### Option 1: PyPI (Recommended - Easiest!)

```bash
# Install from PyPI
pip install musiclist-for-soundiiz

# That's it! Start using it:
musiclist-for-soundiiz -i ~/Music -o output.csv

# Or launch the GUI:
musiclist-for-soundiiz-gui
```

**Prerequisites**: Python 3.8 or higher

For GUI support on Linux:
```bash
sudo apt-get install python3-tk  # Ubuntu/Debian
```

### Option 2: Docker (No Python Required!)

```bash
# Quick start with Docker
docker build -t musiclist-for-soundiiz .

docker run --rm \
  -v /path/to/music:/music:ro \
  -v $(pwd)/output:/output \
  musiclist-for-soundiiz \
  -i /music -o /output/playlist.csv
```

**📖 See [DOCKER.md](DOCKER.md) for complete Docker guide**

### Option 3: From Source (Development)

#### Prerequisites

- Python 3.8 or higher
- **Tkinter** (for GUI, optional):
  - Ubuntu/Debian: `sudo apt-get install python3-tk`
  - macOS: Pre-installed with Python
  - Windows: Pre-installed with Python

#### Install

```bash
# Clone the repository
git clone https://github.com/lucmuss/musiclist-for-soundiiz.git
cd musiclist-for-soundiiz

# Create virtual environment (recommended)
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install package
pip install -e .

# Or with development dependencies
pip install -e ".[dev]"
```

## ⚡ Quick Start

### GUI Version (Recommended for Beginners)

```bash
# Launch the graphical interface
musiclist-for-soundiiz-gui
```

**Features:**
- 🖱️ Easy drag-and-drop interface
- 📊 Real-time progress tracking
- 🎨 Visual duplicate detection
- ✅ No command line knowledge required

### Command Line Version

```bash
# Scan music files and export as CSV
musiclist-for-soundiiz -i /path/to/music -o output.csv

# Result: output.csv (ready for Soundiiz import)
```

## 📚 Usage Examples

### 🖥️ GUI Application

The easiest way to use MusicList for Soundiiz:

```bash
# Start the GUI
musiclist-for-soundiiz-gui
```

**GUI Features:**
1. **Add Directories**: Click "Add Directory" to select music folders
2. **Choose Output**: Select file name and format (CSV, JSON, M3U, TXT)
3. **Options**: Enable duplicate detection, recursive scanning
4. **Process**: Click "Process Files" and watch the progress
5. **Done**: Get visual confirmation and find your exported file

Perfect for users who prefer a visual interface over command line!

### 🎯 Command Line - Basic Usage

```bash
# Scan directory and create CSV
musiclist-for-soundiiz -i /music/library -o soundiiz.csv
```

### 📝 Different Export Formats

```bash
# CSV export (default, for Soundiiz)
musiclist-for-soundiiz -i /music -o playlist.csv -f csv

# JSON export (with all metadata)
musiclist-for-soundiiz -i /music -o playlist.json -f json

# Create M3U playlist
musiclist-for-soundiiz -i /music -o playlist.m3u -f m3u

# Simple text list (Title - Artist)
musiclist-for-soundiiz -i /music -o playlist.txt -f txt
```

### 🎨 Filter by File Type

```bash
# Only MP3 and FLAC files
musiclist-for-soundiiz -i /music -e .mp3 .flac -o output.csv

# Only OGG files
musiclist-for-soundiiz -i /music -e .ogg -o ogg_files.csv
```

### 📁 Non-Recursive Scanning

```bash
# Only current directory (no subdirectories)
musiclist-for-soundiiz -i /music --no-recursive -o output.csv
```

### 🔧 Customize File Splitting

```bash
# Maximum songs per file
musiclist-for-soundiiz -i /music -o output.csv --max-songs-per-file 200

# For more than 200 songs, multiple files are created:
# output_1.csv, output_2.csv, output_3.csv, ...
```

### 🔍 Verbose Mode (Debugging)

```bash
# Detailed output for debugging
musiclist-for-soundiiz -i /music -o output.csv -v

# Or completely silent (errors only)
musiclist-for-soundiiz -i /music -o output.csv -q
```

### 📦 Batch Processing (Multiple Directories)

```bash
# Process multiple directories simultaneously
musiclist-for-soundiiz -i /music/rock /music/pop /music/jazz -o all_music.csv

# Combine music from different sources
musiclist-for-soundiiz -i /external_hdd/music /nas/music /downloads/music -o combined.csv
```

### 🔎 Duplicate Detection

```bash
# Detect duplicates and create report
musiclist-for-soundiiz -i /music --detect-duplicates -o output.csv

# Detect duplicates and save to file
musiclist-for-soundiiz -i /music --detect-duplicates --duplicate-report duplicates.txt -o output.csv

# Automatically remove duplicates (keep first copy)
musiclist-for-soundiiz -i /music --remove-duplicates -o output.csv

# Remove duplicates (keep last copy)
musiclist-for-soundiiz -i /music --remove-duplicates --duplicate-strategy keep_last -o output.csv

# Remove duplicates (keep shortest path)
musiclist-for-soundiiz -i /music --remove-duplicates --duplicate-strategy keep_shortest_path -o output.csv
```

## ⚙️ Configuration

### Command-Line Options

| Option | Description | Default |
|--------|-------------|---------|
| `-i, --input` | Path(s) to music director(y/ies) | **Required** |
| `-o, --output` | Output file path | `output.csv` |
| `-f, --format` | Export format (csv/json/m3u/txt) | `csv` |
| `-e, --extensions` | File extensions to filter | All supported |
| `--no-recursive` | Don't scan subdirectories | `false` |
| `--max-songs-per-file` | Max songs per file | `200` |
| `--no-pretty-json` | Compact JSON (no indentation) | `false` |
| `--detect-duplicates` | Detect and display duplicates | `false` |
| `--remove-duplicates` | Remove duplicates from export | `false` |
| `--duplicate-strategy` | Strategy (keep_first/keep_last/keep_shortest_path) | `keep_first` |
| `--duplicate-report` | Save duplicate report to file | - |
| `-v, --verbose` | Enable verbose logging | `false` |
| `-q, --quiet` | Only show errors | `false` |
| `--version` | Show version | - |

## 📄 Export Formats

### CSV (Soundiiz-compatible)

```csv
title,artist,album,isrc,
Song Title,Artist Name,Album Name,,
Another Song,"Artist, with comma",Album 2,,
```

**Note:** The trailing comma is part of the Soundiiz specification.

### JSON

```json
{
  "total_songs": 2,
  "songs": [
    {
      "title": "Song Title",
      "artist": "Artist Name",
      "album": "Album Name",
      "isrc": "",
      "genre": "Rock",
      "year": "2020",
      "duration": "180",
      "file_path": "/path/to/song.mp3",
      "filename": "song.mp3"
    }
  ]
}
```

### M3U (Playlist)

```
#EXTM3U
#EXTINF:180,Artist Name - Song Title
/path/to/song.mp3
```

### TXT (Simple List)

```
Song Title - Artist Name
Another Song - Another Artist
```

## 🎵 Soundiiz Import

### Step-by-Step Guide

1. **Create CSV file:**
   ```bash
   musiclist-for-soundiiz -i /path/to/music -o my_music.csv
   ```

2. **Go to Soundiiz:**
   - Open [soundiiz.com](https://soundiiz.com)
   - Sign in

3. **Start Import:**
   - Click "Import"
   - Select "CSV File"
   - Upload your `my_music.csv`

4. **Export to Streaming Service:**
   - Select target platform (Spotify, Apple Music, etc.)
   - Confirm export

### Supported Audio Formats

✅ **AAC** (.aac) - Advanced Audio Coding  
✅ **AU** (.au) - AU Audio File  
✅ **FLAC** (.flac) - Free Lossless Audio Codec  
✅ **MP3** (.mp3) - MPEG Audio Layer III  
✅ **OGG** (.ogg) - OGG Vorbis  
✅ **M4A** (.m4a) - MPEG-4 Audio  
✅ **WAV** (.wav) - Waveform Audio File  
✅ **WMA** (.wma) - Windows Media Audio  

## 💻 Development

### Setup Development Environment

```bash
# Clone repository
git clone https://github.com/lucmuss/musiclist-for-soundiiz.git
cd musiclist-for-soundiiz

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install development dependencies
pip install -e ".[dev]"
```

### Code Quality

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

## 🧪 Testing

### Run Tests

```bash
# Run all tests
pytest

# With coverage report
pytest --cov=musiclist_for_soundiiz --cov-report=html

# Specific test file
pytest tests/test_extractor.py

# Verbose mode
pytest -v
```

### Test Coverage

The project has a comprehensive test suite:

- ✅ Unit tests for all formats (AAC, AU, FLAC, MP3, OGG)
- ✅ Tests for all export formats (CSV, JSON, M3U, TXT)
- ✅ Tests for error handling
- ✅ Tests for edge cases (special characters, Unicode, etc.)
- ✅ Tests for recursive/non-recursive scanning
- ✅ Tests for duplicate detection
- ✅ Tests for batch processing

## 📊 Project Structure

```
musiclist-for-soundiiz/
├── src/
│   └── musiclist_for_soundiiz/
│       ├── __init__.py
│       ├── cli.py                 # Command-line interface
│       ├── extractor.py           # Metadata extraction
│       ├── exporter.py            # Export functionality
│       └── duplicate_detector.py  # Duplicate detection
├── tests/
│   ├── __init__.py
│   ├── test_extractor.py          # Extractor tests
│   ├── test_exporter.py           # Exporter tests
│   ├── test_duplicate_detector.py # Duplicate detection tests
│   ├── test_cli.py                # CLI tests
│   └── test_integration.py        # Integration tests
├── .github/
│   └── workflows/
│       └── ci.yml                 # GitHub Actions CI/CD
├── setup.py                       # Package configuration
├── requirements.txt               # Dependencies
├── requirements-dev.txt           # Dev dependencies
├── mypy.ini                       # MyPy configuration
├── .gitignore
├── LICENSE
├── CONTRIBUTING.md
└── README.md
```

## 🤝 Contributing

Contributions are welcome! See [CONTRIBUTING.md](CONTRIBUTING.md) for details.

### Quick Steps

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Add tests
5. Run tests (`pytest`)
6. Commit (`git commit -m 'feat: add amazing feature'`)
7. Push (`git push origin feature/amazing-feature`)
8. Create a Pull Request

## 📝 License

This project is licensed under the MIT License - see [LICENSE](LICENSE) for details.

## 🙏 Acknowledgments

Created with:
- [Mutagen](https://github.com/quodlibet/mutagen) - Python Audio Metadata Library
- [pytest](https://pytest.org/) - Testing Framework

## 📞 Support

- **Issues:** [GitHub Issues](https://github.com/lucmuss/musiclist-for-soundiiz/issues)
- **Discussions:** [GitHub Discussions](https://github.com/lucmuss/musiclist-for-soundiiz/discussions)
- **Documentation:** [README](https://github.com/lucmuss/musiclist-for-soundiiz#readme)

## 🗺️ Roadmap

- [ ] GUI Interface (tkinter/PyQt)
- [ ] Direct Spotify/Apple Music integration
- [ ] Docker Container
- [ ] Web Interface
- [ ] Intelligent genre detection
- [ ] Playlist analysis and statistics

## 💡 Examples

### Process Large Music Library

```bash
# Scan 10,000+ songs and split into multiple CSV files
musiclist-for-soundiiz -i /large/library -o playlist.csv --max-songs-per-file 500
# Creates: playlist_1.csv, playlist_2.csv, playlist_3.csv, ...
```

### Lossless Formats Only

```bash
# Only FLAC and WAV
musiclist-for-soundiiz -i /music -e .flac .wav -o lossless.csv
```

### Complete Export (All Formats)

```bash
# CSV for Soundiiz
musiclist-for-soundiiz -i /music -o soundiiz.csv -f csv

# JSON for backup/analysis
musiclist-for-soundiiz -i /music -o backup.json -f json

# M3U for media player
musiclist-for-soundiiz -i /music -o playlist.m3u -f m3u
```

### Find Duplicates in Large Library

```bash
# Find duplicates and create detailed report
musiclist-for-soundiiz -i /large/library \
  --detect-duplicates \
  --duplicate-report dups.txt \
  -o clean.csv

# Automatically remove duplicates and export clean list
musiclist-for-soundiiz -i /large/library \
  --remove-duplicates \
  --duplicate-strategy keep_shortest_path \
  -o clean_playlist.csv
```

### Combine Multiple Music Sources

```bash
# Combine music from multiple hard drives/folders
musiclist-for-soundiiz \
  -i /mnt/hdd1/music /mnt/hdd2/music /home/user/Downloads/music \
  --remove-duplicates \
  -o combined.csv
```

---

**Developed with ❤️ for the music community**
