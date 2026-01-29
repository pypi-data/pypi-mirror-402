# GUI Installation Guide

## Problem: ModuleNotFoundError: No module named 'tkinter'

Tkinter is usually not included in Python virtual environments. Here's the solution:

---

## ✅ Solution: Install Tkinter System-Wide

### Ubuntu/Debian:
```bash
sudo apt-get update
sudo apt-get install python3-tk
```

### Fedora/RHEL:
```bash
sudo dnf install python3-tkinter
```

### macOS:
```bash
# Tkinter is usually pre-installed with Python
# If not:
brew install python-tk
```

### Windows:
Tkinter is installed by default with Python. No additional steps needed.

---

## 🧪 Test if Tkinter is Installed:

```bash
python3 -m tkinter
```

✅ **Success**: A small test window should appear  
❌ **Error**: Tkinter is not installed

---

## 🚀 After Installation:

```bash
# Navigate to your project directory
cd /home/skymuss/projects/musiclist-for-soundiiz

# Activate virtual environment
source venv/bin/activate

# Start the GUI
musiclist-for-soundiiz-gui
```

---

## 🔧 Alternative: Start GUI Without Installation

If you cannot install Tkinter, start the GUI directly from system Python:

```bash
# WITHOUT virtual environment
cd /home/skymuss/projects/musiclist-for-soundiiz

# Install only Mutagen system-wide
pip3 install mutagen --user

# Start GUI directly
python3 src/musiclist_for_soundiiz/gui.py
```

**Note**: This works because Tkinter is available system-wide, even if it's not in the venv.

---

## 📝 Why Does This Happen?

- Tkinter is a C-extension
- Virtual environments don't copy it automatically
- Must be installed system-wide
- But: Works in all venvs once installed

---

## ✅ Quick Step-by-Step Solution

```bash
# 1. Install Tkinter (requires sudo/admin)
sudo apt-get install python3-tk

# 2. Test
python3 -m tkinter

# 3. Start GUI
cd /home/skymuss/projects/musiclist-for-soundiiz
source venv/bin/activate
musiclist-for-soundiiz-gui
```

---

## 🆘 Still Having Issues?

### Check 1: Python Version
```bash
python3 --version
# GUI requires Python 3.8+
```

### Check 2: Tkinter Version
```bash
python3 -c "import tkinter; print(tkinter.TkVersion)"
# Should be 8.6 or higher
```

### Check 3: Paths
```bash
which python3
which musiclist-for-soundiiz-gui
```

---

## 💡 Tip: Include in Documentation

Add this to your README under "Prerequisites":

```markdown
## Prerequisites

- Python 3.8 or higher
- Tkinter (for GUI):
  - Ubuntu/Debian: `sudo apt-get install python3-tk`
  - macOS: Pre-installed with Python
  - Windows: Pre-installed with Python
```

---

**Problem solved? Start the GUI and have fun! 🎉**
