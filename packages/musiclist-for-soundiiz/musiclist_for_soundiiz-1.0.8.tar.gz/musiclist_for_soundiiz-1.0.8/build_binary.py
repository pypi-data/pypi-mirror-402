#!/usr/bin/env python3
"""
Build script for creating standalone executables with PyInstaller.

Usage:
    python build_binary.py
"""

import os
import platform
import shutil
import subprocess
import sys
from pathlib import Path


def get_platform_name():
    """Get normalized platform name."""
    system = platform.system().lower()
    machine = platform.machine().lower()
    
    if system == "windows":
        return "windows-x64" if "64" in machine else "windows-x86"
    elif system == "darwin":
        return "macos-universal"
    elif system == "linux":
        return f"linux-{machine}"
    return f"{system}-{machine}"


def install_pyinstaller():
    """Install PyInstaller if not already installed."""
    try:
        import PyInstaller
        print(f"[OK] PyInstaller {PyInstaller.__version__} already installed")
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
        print("[OK] PyInstaller installed")


def clean_build_dirs():
    """Clean previous build artifacts."""
    dirs_to_clean = ["build", "dist"]
    for dir_name in dirs_to_clean:
        if Path(dir_name).exists():
            print(f"Cleaning {dir_name}/...")
            shutil.rmtree(dir_name)
    print("[OK] Build directories cleaned")


def build_cli():
    """Build CLI executable."""
    print("\n[*] Building CLI executable...")
    
    cmd = [
        "pyinstaller",
        "--name=musiclist-for-soundiiz",
        "--onefile",
        "--console",
        "--clean",
        "--noconfirm",
        "--add-data=LICENSE:.",
        "--add-data=README.md:.",
        "--hidden-import=mutagen",
        "--hidden-import=mutagen.mp3",
        "--hidden-import=mutagen.flac",
        "--hidden-import=mutagen.oggvorbis",
        "--hidden-import=mutagen.mp4",
        "--hidden-import=mutagen.wave",
        "--hidden-import=mutagen.aac",
        "--collect-all=mutagen",
        "--paths=src",
        "cli_entrypoint.py"
    ]
    
    subprocess.check_call(cmd)
    print("[OK] CLI executable built")


def build_gui():
    """Build GUI executable."""
    print("\n[*] Building GUI executable...")
    
    cmd = [
        "pyinstaller",
        "--name=musiclist-for-soundiiz-gui",
        "--onefile",
        "--windowed" if platform.system() == "Windows" else "--console",
        "--clean",
        "--noconfirm",
        "--add-data=LICENSE:.",
        "--add-data=README.md:.",
        "--hidden-import=mutagen",
        "--hidden-import=mutagen.mp3",
        "--hidden-import=mutagen.flac",
        "--hidden-import=mutagen.oggvorbis",
        "--hidden-import=mutagen.mp4",
        "--hidden-import=mutagen.wave",
        "--hidden-import=mutagen.aac",
        "--hidden-import=tkinter",
        "--collect-all=mutagen",
        "--paths=src",
        "gui_entrypoint.py"
    ]
    
    subprocess.check_call(cmd)
    print("[OK] GUI executable built")


def create_release_package():
    """Create a release package with binaries and documentation."""
    platform_name = get_platform_name()
    release_dir = Path(f"dist/musiclist-for-soundiiz-{platform_name}")
    
    if release_dir.exists():
        shutil.rmtree(release_dir)
    
    release_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"\n[PKG] Creating release package: {release_dir}")
    
    # Copy executables
    dist_path = Path("dist")
    for exe in dist_path.glob("musiclist-for-soundiiz*"):
        if exe.is_file() and exe.name != release_dir.name:
            shutil.copy2(exe, release_dir)
            print(f"  [OK] {exe.name}")
    
    # Copy documentation
    docs = ["README.md", "LICENSE", "DOCKER.md"]
    for doc in docs:
        if Path(doc).exists():
            shutil.copy2(doc, release_dir)
            print(f"  [OK] {doc}")
    
    # Create quick start guide
    quickstart = release_dir / "QUICKSTART.txt"
    with open(quickstart, "w") as f:
        f.write("""MusicList for Soundiiz - Quick Start
=====================================

CLI Usage:
----------
./musiclist-for-soundiiz -i /path/to/music -o output.csv

GUI Usage:
----------
./musiclist-for-soundiiz-gui

Examples:
---------
# Basic scan
./musiclist-for-soundiiz -i ~/Music -o playlist.csv

# With options
./musiclist-for-soundiiz -i ~/Music -o playlist.json -f json --remove-duplicates

# Custom split
./musiclist-for-soundiiz -i ~/Music -o output.csv --max-songs-per-file 500

For full documentation, see README.md
""")
    print(f"  [OK] QUICKSTART.txt")
    
    # Create archive
    archive_name = f"musiclist-for-soundiiz-{platform_name}"
    print(f"\n[PKG] Creating archive: {archive_name}.zip")
    
    shutil.make_archive(
        str(dist_path / archive_name),
        "zip",
        release_dir.parent,
        release_dir.name
    )
    
    print(f"[OK] Release package created: dist/{archive_name}.zip")
    
    # Print file sizes
    print("\n[INFO] File sizes:")
    for exe in release_dir.glob("musiclist-for-soundiiz*"):
        size_mb = exe.stat().st_size / (1024 * 1024)
        print(f"  {exe.name}: {size_mb:.1f} MB")


def main():
    """Main build process."""
    print("[*] MusicList for Soundiiz - Binary Build\n")
    print(f"Platform: {get_platform_name()}")
    print(f"Python: {sys.version.split()[0]}\n")
    
    try:
        # Install PyInstaller
        install_pyinstaller()
        
        # Clean previous builds
        clean_build_dirs()
        
        # Build executables
        build_cli()
        build_gui()
        
        # Create release package
        create_release_package()
        
        print("\n[OK] Build completed successfully!\n")
        print("[PKG] Artifacts:")
        print("  - dist/musiclist-for-soundiiz (CLI)")
        print("  - dist/musiclist-for-soundiiz-gui (GUI)")
        print(f"  - dist/musiclist-for-soundiiz-{get_platform_name()}.zip (Release package)")
        
    except Exception as e:
        print(f"\n[ERROR] Build failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
