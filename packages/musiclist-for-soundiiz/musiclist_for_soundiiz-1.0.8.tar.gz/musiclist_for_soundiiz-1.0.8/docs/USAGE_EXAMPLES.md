# Usage Examples

Common use cases and examples for MusicList for Soundiiz.

## Table of Contents
- [Basic Usage](#basic-usage)
- [Advanced Scenarios](#advanced-scenarios)
- [Large Music Libraries](#large-music-libraries)
- [Duplicate Management](#duplicate-management)
- [Multi-Format Export](#multi-format-export)
- [Docker Workflows](#docker-workflows)
- [Automation](#automation)

## Basic Usage

### Example 1: Simple Playlist Export

**Scenario**: You have a music folder and want to create a CSV for Soundiiz.

#### GUI
1. Launch `musiclist-for-soundiiz-gui`
2. Click "Add Directory" and select `~/Music`
3. Set output file: `playlist.csv`
4. Click "Process Files"

#### CLI
```bash
musiclist-for-soundiiz -i ~/Music -o playlist.csv
```

**Result**: `playlist.csv` containing all songs with metadata ready for Soundiiz import.

---

### Example 2: Scan Multiple Directories

**Scenario**: Your music is spread across multiple folders.

#### GUI
1. Add multiple directories:
   - `~/Music/iTunes`
   - `~/Music/Spotify`
   - `/media/external/Music`
2. Process as usual

#### CLI
```bash
musiclist-for-soundiiz \
  -i ~/Music/iTunes \
  -i ~/Music/Spotify \
  -i /media/external/Music \
  -o combined-library.csv
```

**Result**: All songs from all directories in one CSV file.

---

### Example 3: JSON Export

**Scenario**: You prefer JSON format for better readability.

#### GUI
1. Add your music directory
2. Select "JSON" format
3. Set output: `music-library.json`
4. Process

#### CLI
```bash
musiclist-for-soundiiz -i ~/Music -o music-library.json -f json
```

**Result**: JSON file with detailed metadata for each song.

---

## Advanced Scenarios

### Example 4: Recursive vs Non-Recursive Scanning

**Scenario**: Only scan top-level folders, not subdirectories.

#### GUI
1. Add directory
2. **Uncheck** "Scan subdirectories recursively"
3. Process

#### CLI
```bash
# Non-recursive (only specified directory)
musiclist-for-soundiiz -i ~/Music -o output.csv --no-recursive

# Recursive (default, includes all subdirectories)
musiclist-for-soundiiz -i ~/Music -o output.csv --recursive
```

**Use Case**: When you have organized folders and want to process each separately.

---

### Example 5: Split Large Playlists

**Scenario**: You have 5,000 songs but Soundiiz has a limit of 500 songs per import.

#### GUI
1. Add directory
2. Set "Max songs per file" to `500`
3. Process

#### CLI
```bash
musiclist-for-soundiiz -i ~/Music -o playlist.csv --max-songs-per-file 500
```

**Result**: 
- `playlist_part1.csv` (songs 1-500)
- `playlist_part2.csv` (songs 501-1000)
- `playlist_part3.csv` (songs 1001-1500)
- etc.

---

### Example 6: M3U Playlist for Media Players

**Scenario**: Create a playlist for VLC or other media players.

#### CLI
```bash
musiclist-for-soundiiz -i ~/Music -o party-mix.m3u -f m3u
```

**Result**: `party-mix.m3u` that can be opened in VLC, Winamp, etc.

---

## Large Music Libraries

### Example 7: Processing 100,000+ Songs

**Scenario**: You have a massive music collection.

#### Best Practices
```bash
# Use JSON for better performance
musiclist-for-soundiiz \
  -i /media/music-library \
  -o huge-library.json \
  -f json \
  --max-songs-per-file 1000 \
  --recursive
```

**Tips**:
- JSON format is faster for large libraries
- Split into chunks of 1000 songs
- Use SSD storage for better I/O performance
- Expect ~10,000 songs per minute processing speed

---

### Example 8: Progress Monitoring

**Scenario**: Long-running scan with progress tracking.

#### GUI
The GUI automatically shows:
- Current file being processed
- Progress bar with percentage
- Estimated time remaining
- Real-time log output

#### CLI with Verbose Output
```bash
musiclist-for-soundiiz -i ~/Music -o output.csv --verbose
```

---

## Duplicate Management

### Example 9: Detect Duplicates

**Scenario**: Find duplicate songs in your library.

#### GUI
1. Add directory
2. **Check** "Detect duplicates"
3. Process
4. Review log for duplicate groups

#### CLI
```bash
musiclist-for-soundiiz \
  -i ~/Music \
  -o music.csv \
  --detect-duplicates
```

**Output in Log**:
```
Found 25 duplicate groups (75 total duplicates)
Group 1: "Bohemian Rhapsody" by Queen
  - /Music/Rock/Queen/song.mp3
  - /Music/Classic/Queen - Best Of/song.mp3
  - /Music/Downloads/bohemian.mp3
```

---

### Example 10: Remove Duplicates (Keep First)

**Scenario**: Automatically remove duplicates, keeping the first occurrence.

#### GUI
1. Add directory
2. **Check** "Detect duplicates"
3. **Check** "Remove duplicates"
4. Select strategy: "keep_first"
5. Process

#### CLI
```bash
musiclist-for-soundiiz \
  -i ~/Music \
  -o clean-library.csv \
  --remove-duplicates \
  --duplicate-strategy keep_first
```

**Result**: CSV with no duplicates, keeping first found version.

---

### Example 11: Keep Shortest Path

**Scenario**: Keep the duplicate with the shortest file path.

#### CLI
```bash
musiclist-for-soundiiz \
  -i ~/Music \
  -o output.csv \
  --remove-duplicates \
  --duplicate-strategy keep_shortest_path
```

**Logic**: Prefers `/Music/song.mp3` over `/Music/subfolder1/subfolder2/song.mp3`

---

## Multi-Format Export

### Example 12: Export to All Formats

**Scenario**: Create exports in multiple formats for different uses.

#### Bash Script
```bash
#!/bin/bash
MUSIC_DIR=~/Music

# CSV for Soundiiz
musiclist-for-soundiiz -i $MUSIC_DIR -o soundiiz.csv -f csv

# JSON for backup/analysis
musiclist-for-soundiiz -i $MUSIC_DIR -o library.json -f json

# M3U for media players
musiclist-for-soundiiz -i $MUSIC_DIR -o playlist.m3u -f m3u

# TXT for simple listing
musiclist-for-soundiiz -i $MUSIC_DIR -o songlist.txt -f txt

echo "All exports complete!"
```

---

## Docker Workflows

### Example 13: Docker One-Liner

**Scenario**: Quick scan using Docker without installation.

```bash
docker run -v ~/Music:/music -v ~/output:/output \
  lucmuss/musiclist-for-soundiiz \
  -i /music -o /output/playlist.csv
```

---

### Example 14: Docker Compose with Multiple Directories

**docker-compose.yml**:
```yaml
version: '3.8'

services:
  musiclist:
    image: lucmuss/musiclist-for-soundiiz
    volumes:
      - ~/Music:/music/main
      - /media/external/Music:/music/external
      - ./output:/output
    command: >
      -i /music/main
      -i /music/external
      -o /output/combined.csv
      --remove-duplicates
```

Run:
```bash
docker-compose up
```

---

### Example 15: Automated Docker Backup

**Scenario**: Daily backup of music library metadata.

**cron-job.sh**:
```bash
#!/bin/bash
DATE=$(date +%Y%m%d)

docker run -v ~/Music:/music -v ~/backups:/output \
  lucmuss/musiclist-for-soundiiz \
  -i /music \
  -o /output/music-library-$DATE.json \
  -f json \
  --remove-duplicates

# Keep only last 7 days
find ~/backups -name "music-library-*.json" -mtime +7 -delete
```

Add to crontab:
```bash
0 2 * * * /path/to/cron-job.sh
```

---

## Automation

### Example 16: Python Integration

```python
import subprocess
import json

def extract_music_metadata(music_dir, output_file):
    """Extract music metadata using musiclist-for-soundiiz."""
    cmd = [
        'musiclist-for-soundiiz',
        '-i', music_dir,
        '-o', output_file,
        '-f', 'json',
        '--remove-duplicates'
    ]
    
    result = subprocess.run(cmd, capture_output=True, text=True)
    
    if result.returncode == 0:
        with open(output_file, 'r') as f:
            return json.load(f)
    else:
        raise Exception(f"Error: {result.stderr}")

# Usage
metadata = extract_music_metadata('~/Music', 'library.json')
print(f"Found {len(metadata)} songs")
```

---

### Example 17: Batch Processing Multiple Libraries

```bash
#!/bin/bash

# Array of music directories
DIRS=(
    "/music/library1"
    "/music/library2"
    "/music/library3"
)

# Process each directory
for DIR in "${DIRS[@]}"; do
    NAME=$(basename "$DIR")
    echo "Processing $NAME..."
    
    musiclist-for-soundiiz \
        -i "$DIR" \
        -o "exports/${NAME}.csv" \
        --remove-duplicates \
        --max-songs-per-file 500
        
    echo "✓ $NAME complete"
done

echo "All libraries processed!"
```

---

### Example 18: Integration with Soundiiz API

```python
import requests
import subprocess
import json

def upload_to_soundiiz(csv_file, api_token):
    """Upload playlist to Soundiiz via their API."""
    
    # First, extract metadata
    subprocess.run([
        'musiclist-for-soundiiz',
        '-i', '~/Music',
        '-o', csv_file,
        '-f', 'csv',
        '--remove-duplicates'
    ])
    
    # Then upload to Soundiiz (example - check Soundiiz API docs)
    with open(csv_file, 'rb') as f:
        response = requests.post(
            'https://api.soundiiz.com/v1/playlist/import',
            headers={'Authorization': f'Bearer {api_token}'},
            files={'file': f}
        )
    
    return response.json()
```

---

## Best Practices

### Performance Tips

1. **SSD vs HDD**: 3-5x faster on SSD
2. **Network Drives**: Avoid scanning over network (slow)
3. **Format Choice**:
   - CSV: Best for Soundiiz import
   - JSON: Best for large libraries and backups
   - M3U: Best for media players
   - TXT: Best for simple listings

### Memory Usage

- ~100 MB per 10,000 songs
- Use `--max-songs-per-file` for very large libraries
- JSON format uses slightly more memory than CSV

### Recommended Settings

**For typical use** (5,000-10,000 songs):
```bash
musiclist-for-soundiiz -i ~/Music -o playlist.csv
```

**For large libraries** (50,000+ songs):
```bash
musiclist-for-soundiiz \
  -i ~/Music \
  -o library.json \
  -f json \
  --max-songs-per-file 2000 \
  --remove-duplicates
```

**For quick testing**:
```bash
musiclist-for-soundiiz \
  -i ~/Music/TestFolder \
  -o test.csv \
  --no-recursive
```

---

## Troubleshooting Common Scenarios

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed error solutions.

### Quick Fixes

**No songs found?**
- Check if directory contains supported formats (MP3, FLAC, OGG, AAC, etc.)
- Ensure `--recursive` is enabled for subdirectories

**Out of memory?**
- Use `--max-songs-per-file` to split output
- Switch to JSON format

**Slow processing?**
- Move files to local SSD
- Reduce metadata extraction (use simpler format)

---

## Need Help?

- 📖 [README](../README.md) - General overview
- 🐛 [TROUBLESHOOTING](TROUBLESHOOTING.md) - Error solutions
- 📸 [SCREENSHOTS](SCREENSHOTS.md) - Visual guide
- 🐳 [DOCKER](../DOCKER.md) - Docker usage
- 💬 [GitHub Issues](https://github.com/lucmuss/musiclist-for-soundiiz/issues) - Report bugs
