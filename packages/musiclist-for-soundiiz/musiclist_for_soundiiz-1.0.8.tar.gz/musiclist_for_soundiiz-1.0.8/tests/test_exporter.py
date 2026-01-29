"""Tests for metadata exporters."""

import json
from pathlib import Path

import pytest

from musiclist_for_soundiiz.exporter import (CSVExporter, JSONExporter,
                                             M3UExporter, TXTExporter,
                                             get_exporter)


@pytest.fixture
def sample_metadata():
    """Sample metadata for testing."""
    return [
        {
            "title": "Song 1",
            "artist": "Artist 1",
            "album": "Album 1",
            "isrc": "ISRC001",
            "genre": "Rock",
            "year": "2020",
            "duration": "180",
            "file_path": "/path/to/song1.mp3",
            "filename": "song1.mp3",
        },
        {
            "title": "Song, with comma",
            "artist": 'Artist "with" quotes',
            "album": "Album 2",
            "isrc": "",
            "genre": "Pop",
            "year": "2021",
            "duration": "200",
            "file_path": "/path/to/song2.mp3",
            "filename": "song2.mp3",
        },
    ]


class TestCSVExporter:
    """Test cases for CSVExporter."""

    def test_csv_export_basic(self, tmp_path, sample_metadata):
        """Test basic CSV export."""
        exporter = CSVExporter()
        output_file = tmp_path / "output.csv"

        exporter.export(sample_metadata, str(output_file))

        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")

        # Check header
        assert content.startswith("title,artist,album,isrc,\n")

        # Check that songs are present
        assert "Song 1" in content
        assert "Artist 1" in content

    def test_csv_export_with_commas_and_quotes(self, tmp_path, sample_metadata):
        """Test CSV export with special characters."""
        exporter = CSVExporter()
        output_file = tmp_path / "output.csv"

        exporter.export(sample_metadata, str(output_file))

        content = output_file.read_text(encoding="utf-8")

        # Check proper escaping
        assert '"Song, with comma"' in content
        assert '"Artist ""with"" quotes"' in content

    def test_csv_export_single_file(self, tmp_path, sample_metadata):
        """Test CSV export to single file."""
        exporter = CSVExporter(max_songs_per_file=500)
        output_file = tmp_path / "output.csv"

        exporter.export(sample_metadata, str(output_file))

        # Should create only one file
        csv_files = list(tmp_path.glob("*.csv"))
        assert len(csv_files) == 1

    def test_csv_export_multiple_files(self, tmp_path):
        """Test CSV export split into multiple files."""
        # Create metadata with more songs than max_songs_per_file
        metadata = [
            {
                "title": f"Song {i}",
                "artist": f"Artist {i}",
                "album": f"Album {i}",
                "isrc": "",
            }
            for i in range(5)
        ]

        exporter = CSVExporter(max_songs_per_file=2)
        output_file = tmp_path / "output.csv"

        exporter.export(metadata, str(output_file))

        # Should create 3 files (2+2+1)
        csv_files = sorted(tmp_path.glob("output_*.csv"))
        assert len(csv_files) == 3

        # Check filenames
        assert (tmp_path / "output_1.csv").exists()
        assert (tmp_path / "output_2.csv").exists()
        assert (tmp_path / "output_3.csv").exists()

    def test_csv_export_empty_metadata(self, tmp_path, caplog):
        """Test CSV export with empty metadata list."""
        exporter = CSVExporter()
        output_file = tmp_path / "output.csv"

        exporter.export([], str(output_file))

        # Should log warning
        assert "No metadata to export" in caplog.text

        # Should not create file
        assert not output_file.exists()

    def test_csv_escape_method(self):
        """Test CSV escaping method."""
        exporter = CSVExporter()

        # No special characters - no escaping
        assert exporter._escape_csv("Simple text") == "Simple text"

        # With comma - wrap in quotes
        assert exporter._escape_csv("Text, with comma") == '"Text, with comma"'

        # With quotes - double them and wrap
        assert exporter._escape_csv('Text "with" quotes') == '"Text ""with"" quotes"'

    def test_csv_export_creates_directory(self, tmp_path):
        """Test that CSV exporter creates output directory if it doesn't exist."""
        exporter = CSVExporter()
        output_file = tmp_path / "subdir" / "output.csv"
        metadata = [{"title": "Test", "artist": "Test", "album": "Test", "isrc": ""}]

        exporter.export(metadata, str(output_file))

        assert output_file.exists()


class TestJSONExporter:
    """Test cases for JSONExporter."""

    def test_json_export_basic(self, tmp_path, sample_metadata):
        """Test basic JSON export."""
        exporter = JSONExporter()
        output_file = tmp_path / "output.json"

        exporter.export(sample_metadata, str(output_file))

        assert output_file.exists()

        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "total_songs" in data
        assert data["total_songs"] == 2
        assert "songs" in data
        assert len(data["songs"]) == 2

    def test_json_export_pretty(self, tmp_path, sample_metadata):
        """Test JSON export with pretty formatting."""
        exporter = JSONExporter(pretty=True)
        output_file = tmp_path / "output.json"

        exporter.export(sample_metadata, str(output_file))

        content = output_file.read_text(encoding="utf-8")

        # Pretty format should have indentation
        assert "  " in content

    def test_json_export_compact(self, tmp_path, sample_metadata):
        """Test JSON export without pretty formatting."""
        exporter = JSONExporter(pretty=False)
        output_file = tmp_path / "output.json"

        exporter.export(sample_metadata, str(output_file))

        content = output_file.read_text(encoding="utf-8")

        # Compact format should not have much whitespace
        # Just check it's valid JSON
        data = json.loads(content)
        assert data["total_songs"] == 2

    def test_json_export_empty_metadata(self, tmp_path, caplog):
        """Test JSON export with empty metadata list."""
        exporter = JSONExporter()
        output_file = tmp_path / "output.json"

        exporter.export([], str(output_file))

        assert "No metadata to export" in caplog.text
        assert not output_file.exists()

    def test_json_export_unicode(self, tmp_path):
        """Test JSON export with unicode characters."""
        metadata = [
            {
                "title": "Über den Wolken",
                "artist": "Künstler",
                "album": "Äöü",
                "isrc": "",
            }
        ]

        exporter = JSONExporter()
        output_file = tmp_path / "output.json"

        exporter.export(metadata, str(output_file))

        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert data["songs"][0]["title"] == "Über den Wolken"


class TestM3UExporter:
    """Test cases for M3UExporter."""

    def test_m3u_export_extended(self, tmp_path, sample_metadata):
        """Test M3U export with extended format."""
        exporter = M3UExporter(extended=True)
        output_file = tmp_path / "playlist.m3u"

        exporter.export(sample_metadata, str(output_file))

        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")

        # Check extended M3U header
        assert content.startswith("#EXTM3U\n")

        # Check EXTINF lines
        assert "#EXTINF:180,Artist 1 - Song 1" in content
        assert "/path/to/song1.mp3" in content

    def test_m3u_export_simple(self, tmp_path, sample_metadata):
        """Test M3U export without extended format."""
        exporter = M3UExporter(extended=False)
        output_file = tmp_path / "playlist.m3u"

        exporter.export(sample_metadata, str(output_file))

        content = output_file.read_text(encoding="utf-8")

        # Should not have extended header
        assert not content.startswith("#EXTM3U")

        # Should have file paths
        assert "/path/to/song1.mp3" in content
        assert "/path/to/song2.mp3" in content

    def test_m3u_export_empty_metadata(self, tmp_path, caplog):
        """Test M3U export with empty metadata list."""
        exporter = M3UExporter()
        output_file = tmp_path / "playlist.m3u"

        exporter.export([], str(output_file))

        assert "No metadata to export" in caplog.text
        assert not output_file.exists()


class TestTXTExporter:
    """Test cases for TXTExporter."""

    def test_txt_export_basic(self, tmp_path, sample_metadata):
        """Test basic TXT export."""
        exporter = TXTExporter()
        output_file = tmp_path / "output.txt"

        exporter.export(sample_metadata, str(output_file))

        assert output_file.exists()
        content = output_file.read_text(encoding="utf-8")

        # Check format: Title - Artist
        assert "Song 1 - Artist 1\n" in content
        assert 'Song, with comma - Artist "with" quotes\n' in content

    def test_txt_export_empty_metadata(self, tmp_path, caplog):
        """Test TXT export with empty metadata list."""
        exporter = TXTExporter()
        output_file = tmp_path / "output.txt"

        exporter.export([], str(output_file))

        assert "No metadata to export" in caplog.text
        assert not output_file.exists()


class TestGetExporter:
    """Test cases for get_exporter factory function."""

    def test_get_csv_exporter(self):
        """Test getting CSV exporter."""
        exporter = get_exporter("csv")
        assert isinstance(exporter, CSVExporter)

    def test_get_json_exporter(self):
        """Test getting JSON exporter."""
        exporter = get_exporter("json")
        assert isinstance(exporter, JSONExporter)

    def test_get_m3u_exporter(self):
        """Test getting M3U exporter."""
        exporter = get_exporter("m3u")
        assert isinstance(exporter, M3UExporter)

    def test_get_txt_exporter(self):
        """Test getting TXT exporter."""
        exporter = get_exporter("txt")
        assert isinstance(exporter, TXTExporter)

    def test_get_exporter_case_insensitive(self):
        """Test that format is case-insensitive."""
        exporter = get_exporter("CSV")
        assert isinstance(exporter, CSVExporter)

    def test_get_exporter_with_kwargs(self):
        """Test getting exporter with additional arguments."""
        exporter = get_exporter("csv", max_songs_per_file=100)
        assert isinstance(exporter, CSVExporter)
        assert exporter.max_songs_per_file == 100

    def test_get_exporter_invalid_format(self):
        """Test getting exporter with invalid format."""
        with pytest.raises(ValueError) as exc_info:
            get_exporter("invalid")

        assert "Unsupported format" in str(exc_info.value)
