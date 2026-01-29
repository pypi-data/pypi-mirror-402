# 📦 Pre-built Binaries

Download and run - **no Python installation required!**

## 🚀 Quick Start

### Download

Visit the [Releases page](https://github.com/lucmuss/musiclist-for-soundiiz/releases) and download the binary for your platform:

- **Windows**: `musiclist-for-soundiiz-windows-x64.zip`
- **macOS**: `musiclist-for-soundiiz-macos-universal.zip`
- **Linux**: `musiclist-for-soundiiz-linux-x86_64.zip`

### Extract and Run

```bash
# Extract the archive
unzip musiclist-for-soundiiz-*.zip
cd musiclist-for-soundiiz-*/

# Run CLI
./musiclist-for-soundiiz -i ~/Music -o output.csv

# Run GUI
./musiclist-for-soundiiz-gui
```

## 💻 Platform-Specific Instructions

### Windows

1. Download `musiclist-for-soundiiz-windows-x64.zip`
2. Extract using Windows Explorer (Right-click → Extract All)
3. Open PowerShell or Command Prompt in that folder
4. Run:
   ```cmd
   musiclist-for-soundiiz.exe -i C:\Users\YourName\Music -o output.csv
   ```

**Note**: Windows might show a SmartScreen warning. Click "More info" → "Run anyway"

### macOS

1. Download `musiclist-for-soundiiz-macos-universal.zip`
2. Extract (double-click in Finder)
3. Open Terminal in that folder
4. Make executable:
   ```bash
   chmod +x musiclist-for-soundiiz musiclist-for-soundiiz-gui
   ```
5. Run:
   ```bash
   ./musiclist-for-soundiiz -i ~/Music -o output.csv
   ```

**Note**: macOS might block the app. Go to System Preferences → Security & Privacy and click "Allow"

### Linux

1. Download `musiclist-for-soundiiz-linux-x86_64.zip`
2. Extract:
   ```bash
   unzip musiclist-for-soundiiz-linux-x86_64.zip
   cd musiclist-for-soundiiz-linux-x86_64/
   ```
3. Make executable:
   ```bash
   chmod +x musiclist-for-soundiiz musiclist-for-soundiiz-gui
   ```
4. Run:
   ```bash
   ./musiclist-for-soundiiz -i ~/Music -o output.csv
   ```

## 📝 Usage Examples

### CLI Examples

```bash
# Basic scan
./musiclist-for-soundiiz -i /path/to/music -o output.csv

# JSON export
./musiclist-for-soundiiz -i /path/to/music -o output.json -f json

# Remove duplicates
./musiclist-for-soundiiz -i /path/to/music -o clean.csv --remove-duplicates

# Custom max songs per file
./musiclist-for-soundiiz -i /path/to/music -o output.csv --max-songs-per-file 500

# Multiple directories
./musiclist-for-soundiiz -i /music/rock /music/pop -o combined.csv

# Verbose mode
./musiclist-for-soundiiz -i /path/to/music -o output.csv -v
```

### GUI

Simply run the GUI executable:

```bash
./musiclist-for-soundiiz-gui
```

The GUI provides:
- 🖱️ Easy drag-and-drop interface
- 📊 Real-time progress tracking
- 🌍 12 languages
- ✅ No command line knowledge required

## 🔐 Security & Verification

### Verify Checksums

Download `SHA256SUMS.txt` from the release and verify:

```bash
# Windows (PowerShell)
Get-FileHash musiclist-for-soundiiz-windows-x64.zip -Algorithm SHA256

# macOS/Linux
sha256sum musiclist-for-soundiiz-*.zip
```

Compare the output with `SHA256SUMS.txt`.

### Why might my OS block the binary?

Pre-built binaries are not code-signed (requires expensive certificates). Your OS might show warnings because:

- **Windows**: SmartScreen filters unsigned apps
- **macOS**: Gatekeeper blocks unsigned apps
- **Linux**: Usually no issues

**Solution**: The binaries are safe (built automatically by GitHub Actions). You can:
1. Check the source code yourself
2. Build from source: `python build_binary.py`
3. Use Docker: `docker run musiclist-for-soundiiz`

## 🔨 Build Your Own

Don't trust pre-built binaries? Build your own:

```bash
# Clone repository
git clone https://github.com/lucmuss/musiclist-for-soundiiz.git
cd musiclist-for-soundiiz

# Install dependencies
pip install -r requirements.txt
pip install pyinstaller

# Build
python build_binary.py

# Find binaries in dist/
```

## 📊 Binary Sizes

Typical sizes (compressed):

- **Windows**: ~15-20 MB
- **macOS**: ~18-25 MB
- **Linux**: ~15-20 MB

Uncompressed executables are larger (~40-60 MB) because they include:
- Python interpreter
- All dependencies (mutagen, tkinter)
- Standard library

## 🆚 Binaries vs Other Methods

| Method | Pros | Cons |
|--------|------|------|
| **Binaries** | ✅ No Python<br>✅ Easy to use<br>✅ Fast start | ❌ Large files<br>❌ One per platform |
| **pip install** | ✅ Small download<br>✅ Easy updates | ❌ Requires Python<br>❌ Setup needed |
| **Docker** | ✅ Consistent<br>✅ Isolated | ❌ Requires Docker<br>❌ Overhead |
| **From source** | ✅ Latest code<br>✅ Customizable | ❌ Requires Python<br>❌ Manual updates |

## 🐛 Troubleshooting

### Binary won't run

**Windows**:
```cmd
# Run in PowerShell
.\musiclist-for-soundiiz.exe --version
```

**macOS/Linux**:
```bash
# Check permissions
ls -l musiclist-for-soundiiz

# Make executable
chmod +x musiclist-for-soundiiz

# Run
./musiclist-for-soundiiz --version
```

### "Permission denied" errors

```bash
# macOS/Linux
chmod +x musiclist-for-soundiiz*

# Windows: Run as Administrator
```

### Missing files error

Make sure you:
1. Extracted the **entire** ZIP file
2. Run from the extracted folder
3. All files (QUICKSTART.txt, README.md, LICENSE) are present

### GUI doesn't start

**Linux**: Install tkinter
```bash
sudo apt-get install python3-tk
```

**macOS/Windows**: Should work out of the box

## 📚 Additional Resources

- [README](README.md) - Full documentation
- [DOCKER.md](DOCKER.md) - Docker usage
- [GitHub](https://github.com/lucmuss/musiclist-for-soundiiz) - Source code
- [Issues](https://github.com/lucmuss/musiclist-for-soundiiz/issues) - Report problems

## 🎯 Why Use Binaries?

✅ **Zero Installation** - Download and run  
✅ **No Dependencies** - Everything included  
✅ **No Python Knowledge** - Just double-click  
✅ **Portable** - Run from USB stick  
✅ **Consistent** - Same behavior everywhere  

---

**Download now and start converting your music library!** 🎵
