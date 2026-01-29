# Screenshots

A visual guide for MusicList for Soundiiz.

## GUI Overview

### Main Window
![GUI Main Window](images/main-window.png)

The main window shows all important functions at a glance:
- **Input Directories**: Select one or more music directories
- **Output**: Target file and format options
- **Options**: Configurations like recursive scanning and duplicate detection
- **Progress**: Real-time status and log output

### Language Selection
![Language Selection](images/language-selector.png)

12 languages are supported:
- English, German, Spanish, French
- Portuguese, Italian, Dutch, Russian
- Japanese, Korean, Chinese, Arabic

### Adding Input Directories
![Adding Directories](images/add-directories.png)

1. Click on "Add Directory"
2. Select your music directory
3. Repeat for multiple directories
4. Use the scrollbar for many folders

### Output Configuration
![Output Settings](images/output-settings.png)

Choose:
- **Format**: CSV, JSON, M3U or TXT
- **Max songs per file**: Automatically split large playlists
- **Output File**: Select target file via "Browse"

### Options
![Advanced Options](images/options.png)

- **Scan subdirectories recursively**: Search all subfolders
- **Detect duplicates**: Find duplicate songs
- **Remove duplicates**: Remove duplicates automatically
- **Strategy**: Choose which duplicates to keep

### Progress Tracking
![Progress Display](images/progress-tracking.png)

Real-time feedback:
- **Status**: Current progress
- **Progress Bar**: Visual progress indicator
- **Estimated Time**: Remaining time
- **Log**: Detailed outputs

### Result
![Successful Processing](images/success.png)

After processing:
- Success message with number of songs
- Log shows all details
- Output file is ready for Soundiiz

## CLI Usage

### Basic Command
```bash
musiclist-for-soundiiz -i ~/Music -o playlist.csv
```
![CLI Basic](images/cli-basic.png)

### With Options
```bash
musiclist-for-soundiiz -i ~/Music -o output.json \
  -f json --remove-duplicates --max-songs-per-file 500
```
![CLI Advanced](images/cli-advanced.png)

### Show Help
```bash
musiclist-for-soundiiz --help
```
![CLI Help](images/cli-help.png)

## Docker Usage

### Start Container
```bash
docker run -v ~/Music:/music -v ~/output:/output \
  musiclist-for-soundiiz -i /music -o /output/playlist.csv
```
![Docker Run](images/docker-run.png)

### Docker Compose
```bash
docker-compose up
```
![Docker Compose](images/docker-compose.png)

## Screenshot Placeholders

To add the screenshots, save them in `docs/images/` with these names:

### GUI Screenshots
- `main-window.png` - Main window at startup
- `language-selector.png` - Language selection dropdown open
- `add-directories.png` - Add directory dialog
- `output-settings.png` - Output area with all options
- `options.png` - Advanced options activated
- `progress-tracking.png` - During processing
- `success.png` - Success message at the end

### CLI Screenshots
- `cli-basic.png` - Simple CLI command
- `cli-advanced.png` - CLI with many options
- `cli-help.png` - Help output

### Docker Screenshots
- `docker-run.png` - Docker container output
- `docker-compose.png` - Docker Compose logs

## Screenshot Guidelines

### For GUI Screenshots:
1. **Resolution**: At least 1280x720
2. **Format**: PNG with transparency or JPG
3. **Window Size**: Standard 850x750 pixels
4. **Sample Data**: Use realistic but anonymized paths
5. **Language**: Create screenshots in English and German

### For CLI Screenshots:
1. **Terminal**: Use a modern terminal emulator
2. **Font**: Monospace, easily readable
3. **Color Scheme**: Light or dark (stay consistent)
4. **Size**: Show only relevant outputs
5. **Highlighting**: Important parts can be highlighted

### For Docker Screenshots:
1. **Container Logs**: Show successful execution
2. **Volumes**: Demonstrate correct volume mounts
3. **Output**: Show generated files

## Screenshot Tools

### macOS
```bash
# Full screen
Cmd + Shift + 3

# Selection
Cmd + Shift + 4

# Window
Cmd + Shift + 4, then Spacebar
```

### Windows
```bash
# Full screen
Win + PrtScn

# Snip (Snipping Tool)
Win + Shift + S
```

### Linux
```bash
# GNOME Screenshot
gnome-screenshot

# Flameshot (recommended)
flameshot gui
```

## Image Editing

After creating the screenshots:

1. **Crop**: Remove unnecessary borders
2. **Annotations**: Add arrows/boxes if needed
3. **Optimize**: Compress for web (PNG: pngquant, JPG: mozjpeg)
4. **Rename**: Use the file names mentioned above

## Video Tutorials (Optional)

For extended documentation, you can also create short videos:
- `tutorial-basic.mp4` - 2-3 minutes basics
- `tutorial-advanced.mp4` - 5 minutes advanced features
- `tutorial-docker.mp4` - Docker setup and usage
