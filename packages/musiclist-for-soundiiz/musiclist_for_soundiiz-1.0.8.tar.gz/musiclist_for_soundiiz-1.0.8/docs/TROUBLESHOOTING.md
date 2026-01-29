# Troubleshooting Guide

Solutions to common problems with MusicList for Soundiiz.

## Table of Contents
- [Installation Issues](#installation-issues)
- [Runtime Errors](#runtime-errors)
- [Performance Problems](#performance-problems)
- [Output Issues](#output-issues)
- [GUI Problems](#gui-problems)
- [Docker Issues](#docker-issues)
- [Platform-Specific Issues](#platform-specific-issues)

---

## Installation Issues

### Python Package Not Found

**Problem**: `Command 'musiclist-for-soundiiz' not found`

**Solutions**:

1. **Check installation**:
```bash
pip show musiclist-for-soundiiz
```

2. **Install/Reinstall**:
```bash
pip install --upgrade musiclist-for-soundiiz
```

3. **Check PATH**:
```bash
# Linux/macOS
echo $PATH | grep -o "[^:]*\.local/bin"

# Windows
echo %PATH%
```

4. **Use module syntax**:
```bash
python -m musiclist_for_soundiiz.cli -i ~/Music -o output.csv
```

---

### Dependency Conflicts

**Problem**: `ERROR: Could not find a version that satisfies the requirement mutagen`

**Solution**:
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# or
venv\Scripts\activate     # Windows

# Install in clean environment
pip install musiclist-for-soundiiz
```

---

### Permission Denied

**Problem**: `Permission denied` during installation

**Solutions**:

**Linux/macOS**:
```bash
# Install for user only
pip install --user musiclist-for-soundiiz

# Or use sudo (not recommended)
sudo pip install musiclist-for-soundiiz
```

**Windows** (Run as Administrator):
```bash
pip install musiclist-for-soundiiz
```

---

## Runtime Errors

### No Music Files Found

**Problem**: `No music files found in directory`

**Diagnosis**:
```bash
# Check if directory exists
ls -la ~/Music

# Check for music files
find ~/Music -type f \( -name "*.mp3" -o -name "*.flac" \) | head -10
```

**Solutions**:

1. **Check directory path**:
```bash
# Use absolute path
musiclist-for-soundiiz -i /home/user/Music -o output.csv
```

2. **Enable recursive scanning**:
```bash
musiclist-for-soundiiz -i ~/Music -o output.csv --recursive
```

3. **Check supported formats**:
```bash
# Supported: MP3, FLAC, OGG, AAC, M4A, WMA, WAV
ls ~/Music/*.{mp3,flac,ogg,aac,m4a,wma,wav}
```

---

### Metadata Extraction Errors

**Problem**: `Error reading metadata from file: /path/to/song.mp3`

**Causes & Solutions**:

1. **Corrupted file**:
```bash
# Test with media player
vlc /path/to/song.mp3

# Re-encode if corrupted
ffmpeg -i corrupted.mp3 -c copy fixed.mp3
```

2. **Unsupported encoding**:
```bash
# Check file details
file /path/to/song.mp3
mediainfo /path/to/song.mp3
```

3. **Permission issues**:
```bash
# Check file permissions
ls -l /path/to/song.mp3

# Fix permissions
chmod 644 /path/to/song.mp3
```

---

### Unicode/Encoding Errors

**Problem**: `UnicodeDecodeError: 'utf-8' codec can't decode byte`

**Solutions**:

1. **Set locale** (Linux/macOS):
```bash
export LANG=en_US.UTF-8
export LC_ALL=en_US.UTF-8
```

2. **Fix file names**:
```bash
# Rename files with special characters
convmv -f iso-8859-1 -t utf-8 -r --notest ~/Music/
```

3. **Use Python 3.8+**:
```bash
python --version  # Should be >= 3.8
```

---

### Out of Memory

**Problem**: `MemoryError` or system freezes during processing

**Solutions**:

1. **Split large libraries**:
```bash
musiclist-for-soundiiz -i ~/Music -o output.csv --max-songs-per-file 1000
```

2. **Process subdirectories separately**:
```bash
for dir in ~/Music/*/; do
    name=$(basename "$dir")
    musiclist-for-soundiiz -i "$dir" -o "${name}.csv" --no-recursive
done
```

3. **Use JSON format** (more memory efficient):
```bash
musiclist-for-soundiiz -i ~/Music -o library.json -f json
```

4. **Increase system RAM or swap**:
```bash
# Linux: Check memory usage
free -h

# Create swap file if needed
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

---

## Performance Problems

### Slow Processing

**Problem**: Processing takes too long

**Diagnosis**:
```bash
# Check disk I/O
iostat -x 1

# Check if using network drive
df -h ~/Music
```

**Solutions**:

1. **Move to local SSD**:
```bash
# Copy to local drive
rsync -avh --progress /network/music/ ~/Music-Local/
```

2. **Disable duplicate detection** (if not needed):
```bash
musiclist-for-soundiiz -i ~/Music -o output.csv
# Don't use --detect-duplicates
```

3. **Process in parallel**:
```bash
#!/bin/bash
# Process subdirectories in parallel
find ~/Music -maxdepth 1 -type d | \
parallel musiclist-for-soundiiz -i {} -o {/}.csv
```

**Expected Performance**:
- SSD: ~10,000 songs/minute
- HDD: ~3,000 songs/minute  
- Network: ~500 songs/minute

---

### High CPU Usage

**Problem**: 100% CPU usage during processing

**This is normal** - metadata extraction is CPU-intensive.

**To limit CPU**:

**Linux**:
```bash
nice -n 19 musiclist-for-soundiiz -i ~/Music -o output.csv
```

**Windows** (Task Manager):
1. Find `python.exe` process
2. Right-click → Set Priority → Below Normal

---

## Output Issues

### Empty Output File

**Problem**: Output CSV/JSON is empty or very small

**Diagnosis**:
```bash
# Check file size
ls -lh output.csv

# View first lines
head -20 output.csv

# Count lines
wc -l output.csv
```

**Solutions**:

1. **Check input directory has music**:
```bash
find ~/Music -name "*.mp3" | wc -l
```

2. **Review logs**:
```bash
musiclist-for-soundiiz -i ~/Music -o output.csv --verbose
```

3. **Test with small directory**:
```bash
musiclist-for-soundiiz -i ~/Music/TestFolder -o test.csv
```

---

### Invalid CSV Format

**Problem**: Soundiiz rejects the CSV file

**Solutions**:

1. **Check CSV format**:
```bash
# Should have header: title,artist,album,duration,filepath
head -1 output.csv
```

2. **Re-export**:
```bash
musiclist-for-soundiiz -i ~/Music -o fresh-export.csv -f csv
```

3. **Use UTF-8 encoding**:
```bash
# Check encoding
file output.csv

# Convert if needed
iconv -f ISO-8859-1 -t UTF-8 output.csv > output-utf8.csv
```

---

### Split Files Not Created

**Problem**: `--max-songs-per-file` not creating multiple files

**Check**:
```bash
# Ensure you have more songs than the limit
ls -1 output_part*.csv

# Try smaller limit
musiclist-for-soundiiz -i ~/Music -o output.csv --max-songs-per-file 10
```

---

## GUI Problems

### GUI Won't Start

**Problem**: `No module named 'tkinter'`

**Solutions**:

**Ubuntu/Debian**:
```bash
sudo apt-get install python3-tk
```

**Fedora/RHEL**:
```bash
sudo dnf install python3-tkinter
```

**macOS**:
```bash
brew install python-tk@3.11
```

**Windows**: Reinstall Python with "tcl/tk" option checked

---

### GUI Freezes During Processing

**This is expected** - GUI uses single thread

**Workaround**: Use CLI instead
```bash
musiclist-for-soundiiz -i ~/Music -o output.csv
```

Or wait for processing to complete - the GUI will become responsive again.

---

### Fonts Look Wrong (CJK Languages)

**Problem**: Chinese/Japanese/Korean characters display incorrectly

**Solutions**:

**Linux**:
```bash
# Install CJK fonts
sudo apt-get install fonts-noto-cjk

# Or
sudo apt-get install fonts-wqy-zenhei
```

**macOS**: Fonts bundled by default

**Windows**: Install language pack from Settings

---

### GUI Window Too Small

**Problem**: Can't see all buttons

**Solutions**:

1. **Resize window**: Drag window edges
2. **Update to latest version** (fixed in v1.0.5+):
```bash
pip install --upgrade musiclist-for-soundiiz
```

---

## Docker Issues

### Container Permission Errors

**Problem**: `Permission denied` when accessing volumes

**Solution**:

```bash
# Run with user permissions
docker run --user $(id -u):$(id -g) \
  -v ~/Music:/music \
  -v ~/output:/output \
  lucmuss/musiclist-for-soundiiz \
  -i /music -o /output/playlist.csv
```

---

### Volume Mount Not Working

**Problem**: Container can't see host files

**Diagnosis**:
```bash
# Test volume
docker run -v ~/Music:/music alpine ls -la /music
```

**Solutions**:

1. **Use absolute paths**:
```bash
docker run -v /home/user/Music:/music ...
# Not: ~/Music
```

2. **Check Docker permissions** (Linux):
```bash
# Add user to docker group
sudo usermod -aG docker $USER
newgrp docker
```

3. **SELinux** (Fedora/RHEL):
```bash
# Add :z flag
docker run -v ~/Music:/music:z ...
```

---

### Out of Memory in Container

**Problem**: Docker container crashes with OOM

**Solution**:

```bash
# Increase Docker memory limit
docker run -m 4g \
  -v ~/Music:/music \
  -v ~/output:/output \
  lucmuss/musiclist-for-soundiiz \
  -i /music -o /output/output.csv --max-songs-per-file 1000
```

---

## Platform-Specific Issues

### Windows

#### Path Issues

**Problem**: `FileNotFoundError` with Windows paths

**Solutions**:

1. **Use forward slashes**:
```bash
musiclist-for-soundiiz -i C:/Users/Music -o output.csv
```

2. **Escape backslashes**:
```bash
musiclist-for-soundiiz -i C:\\Users\\Music -o output.csv
```

3. **Use raw strings** (Python):
```python
input_dir = r"C:\Users\Music"
```

#### Antivirus Blocking

**Problem**: Antivirus quarantines executable

**Solution**: Add exception for:
- `python.exe`
- `Scripts\musiclist-for-soundiiz.exe`

---

### macOS

#### Gatekeeper Blocking

**Problem**: "App can't be opened because it is from an unidentified developer"

**Solution**:
```bash
# Remove quarantine attribute
xattr -d com.apple.quarantine musiclist-for-soundiiz-gui

# Or allow in System Preferences
# System Preferences → Security & Privacy → Allow
```

#### Permission Denied for Music Folder

**Problem**: Can't access `~/Music`

**Solution**:
1. System Preferences → Security & Privacy → Privacy
2. Select "Files and Folders"
3. Grant Python access to Music folder

---

### Linux

#### Missing Dependencies

**Problem**: `ImportError: libpython3.11.so.1.0: cannot open shared object file`

**Solution**:
```bash
# Ubuntu/Debian
sudo apt-get install python3.11 python3.11-dev

# Fedora
sudo dnf install python3.11 python3.11-devel

# Update LD_LIBRARY_PATH
export LD_LIBRARY_PATH=/usr/local/lib:$LD_LIBRARY_PATH
```

#### AppImage Won't Run

**Problem**: Binary doesn't execute

**Solution**:
```bash
# Make executable
chmod +x musiclist-for-soundiiz-gui-x86_64.AppImage

# Install FUSE
sudo apt-get install fuse libfuse2
```

---

## Advanced Troubleshooting

### Enable Debug Mode

```bash
# GUI
export DEBUG=1
musiclist-for-soundiiz-gui

# CLI with verbose output
musiclist-for-soundiiz -i ~/Music -o output.csv --verbose
```

### Check Logs

**Linux/macOS**:
```bash
~/.local/share/musiclist-for-soundiiz/logs/
```

**Windows**:
```
%APPDATA%\musiclist-for-soundiiz\logs\
```

### Report Bug

If problem persists:

1. **Gather information**:
```bash
# System info
uname -a
python --version
pip show musiclist-for-soundiiz

# Test command
musiclist-for-soundiiz -i ~/Music -o test.csv --verbose 2>&1 | tee debug.log
```

2. **Create GitHub Issue**:
   - https://github.com/lucmuss/musiclist-for-soundiiz/issues
   - Include:
     - OS and version
     - Python version
     - Command used
     - Error message
     - `debug.log` file

---

## Common Error Messages

### `mutagen.MutagenError: unsupported format`

**Cause**: File format not supported or corrupted

**Solution**: Skip the file or convert to supported format
```bash
ffmpeg -i unsupported.wma output.mp3
```

---

### `FileNotFoundError: [Errno 2] No such file or directory`

**Cause**: Invalid input path

**Solution**: Check path exists
```bash
ls -la /path/to/music
```

---

### `PermissionError: [Errno 13] Permission denied`

**Cause**: No read/write permissions

**Solution**:
```bash
# Fix input permissions
chmod -R 755 ~/Music

# Fix output directory
chmod 755 ~/output
```

---

## Performance Benchmarks

Normal processing speeds:

| Library Size | Expected Time (SSD) | Expected Time (HDD) |
|---|---|---|
| 1,000 songs | 6 seconds | 20 seconds |
| 10,000 songs | 1 minute | 3-4 minutes |
| 50,000 songs | 5 minutes | 15-20 minutes |
| 100,000 songs | 10 minutes | 30-40 minutes |

If significantly slower, see [Performance Problems](#performance-problems).

---

## Still Need Help?

- 📖 [Usage Examples](USAGE_EXAMPLES.md)
- 📸 [Screenshots](SCREENSHOTS.md)
- 🐳 [Docker Guide](../DOCKER.md)
- 💬 [GitHub Discussions](https://github.com/lucmuss/musiclist-for-soundiiz/discussions)
- 🐛 [Report Bug](https://github.com/lucmuss/musiclist-for-soundiiz/issues/new)
