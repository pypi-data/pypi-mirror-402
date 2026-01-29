# GUI Quick Start Guide 🖥️

## Starting the GUI

### Option 1: After Installation
```bash
musiclist-for-soundiiz-gui
```

### Option 2: Direct Python Execution
```bash
python3 -m musiclist_for_soundiiz.gui
```

### Option 3: From Source
```bash
cd /path/to/musiclist-for-soundiiz
python3 src/musiclist_for_soundiiz/gui.py
```

---

## Using the GUI

### 1️⃣ Add Music Directories
- Click **"Add Directory"** button
- Select your music folder(s)
- Add multiple folders if needed
- Remove unwanted folders with **"Remove Selected"**

### 2️⃣ Choose Output File
- Enter output filename or click **"Browse"**
- Select format: **CSV** (for Soundiiz), **JSON**, **M3U**, or **TXT**

### 3️⃣ Configure Options
- ✅ **Scan subdirectories recursively** - Includes all subfolders
- ✅ **Detect duplicates** - Find duplicate songs
- ✅ **Remove duplicates** - Automatically remove duplicates
  - Strategy: `keep_first`, `keep_last`, or `keep_shortest_path`

### 4️⃣ Process Files
- Click **"🚀 Process Files"**
- Watch the progress bar
- Read the log for details
- Wait for "Success" message

### 5️⃣ Done!
- Your file is ready for Soundiiz import
- Check the log for summary

---

## GUI Features

### 📊 Real-Time Progress
- Live progress bar during processing
- Detailed log showing each step
- Files found counter
- Duplicate detection results

### 🎨 Visual Interface
- Clean, intuitive design
- No command line needed
- Error messages in dialog boxes
- Help and About dialogs

### ⚡ Multi-Directory Support
- Process multiple music folders at once
- Combine libraries from different locations
- Perfect for external drives and NAS

### 🔍 Smart Duplicate Detection
- Case-insensitive matching
- Shows duplicate count
- Multiple removal strategies
- Optional duplicate report

---

## Keyboard Shortcuts

- **Ctrl+A** - Select all in directory list
- **Delete** - Remove selected directories
- **F1** - Show help dialog

---

## Tips & Tricks

### 💡 Best Practices
1. **Start Small**: Test with a small folder first
2. **Use Duplicates**: Enable duplicate detection for large libraries
3. **Watch the Log**: Monitor progress in real-time
4. **Save Often**: Export to multiple formats for backup

### 🚀 Power User Tips
- Add all your music directories at once
- Use duplicate detection to clean your library
- Export to JSON for detailed metadata backup
- Keep the log open to debug issues

---

## Troubleshooting

### GUI Won't Start?
```bash
# Make sure Tkinter is installed (usually comes with Python)
python3 -m tkinter  # Should open a test window

# On Ubuntu/Debian if missing:
sudo apt-get install python3-tk

# On macOS (should be pre-installed)
# On Windows (should be pre-installed with Python)
```

### Files Not Found?
- Check if directory path is correct
- Ensure music files have supported extensions
- Try enabling recursive scanning
- Check the log for error messages

### Duplicate Detection Not Working?
- Files must have title AND artist metadata
- Or use "Artist - Title" filename format
- Check log for duplicate detection results

---

## Screenshots

### Main Window
```
┌─────────────────────────────────────────────┐
│         🎵 MusicList for Soundiiz           │
│  Extract music metadata and create playlists│
├─────────────────────────────────────────────┤
│ 📁 Input Directories                        │
│ ┌─────────────────────────────────────────┐ │
│ │ /music/rock                             │ │
│ │ /music/pop                              │ │
│ │ /music/jazz                             │ │
│ └─────────────────────────────────────────┘ │
│ [Add Directory] [Remove] [Clear All]        │
├─────────────────────────────────────────────┤
│ 📄 Output                                   │
│ Output File: [output.csv          ] [Browse]│
│ Format: (●) CSV  ( ) JSON  ( ) M3U  ( ) TXT │
├─────────────────────────────────────────────┤
│ ⚙️ Options                                  │
│ ☑ Scan subdirectories recursively          │
│ ☑ Detect duplicates                        │
│   ☑ Remove duplicates                      │
│     Strategy: [keep_first ▼]               │
├─────────────────────────────────────────────┤
│ 📊 Progress                                 │
│ Ready                                       │
│ [████████████████████████] 100%             │
│ ┌─────────────────────────────────────────┐ │
│ │ Starting processing...                  │ │
│ │ Scanning: /music/rock                   │ │
│ │   Found 523 files                       │ │
│ │ ✓ Total files found: 523                │ │
│ └─────────────────────────────────────────┘ │
├─────────────────────────────────────────────┤
│ [🚀 Process Files] [Clear Log] [Help] [About]│
├─────────────────────────────────────────────┤
│ Ready to process music files                │
└─────────────────────────────────────────────┘
```

---

## Next Steps

After processing:
1. **Import to Soundiiz**: Upload CSV to soundiiz.com
2. **Backup**: Keep JSON export for complete metadata
3. **Share**: Use M3U playlist in media players

---

**Enjoy the GUI! Questions? Open an issue on GitHub.**
