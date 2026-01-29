"""MusicList for Soundiiz - Extract music file metadata for Soundiiz import."""

__version__ = "1.0.8"
__author__ = "Luc Muss"
__license__ = "MIT"

from .cli import main
from .exporter import CSVExporter, JSONExporter, M3UExporter
from .extractor import MusicFileExtractor

__all__ = [
    "main",
    "MusicFileExtractor",
    "CSVExporter",
    "JSONExporter",
    "M3UExporter",
]
