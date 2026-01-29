#!/usr/bin/env python3
"""Entry point wrapper for PyInstaller builds."""

import sys
from musiclist_for_soundiiz.cli import main

if __name__ == "__main__":
    sys.exit(main())
