"""Tests for music file metadata extraction."""

from pathlib import Path

import pytest

from musiclist_for_soundiiz.extractor import MusicFileExtractor


class TestMusicFileExtractor:
    """Test cases for MusicFileExtractor class."""

    def test_supported_extensions(self):
        """Test that all required audio formats are supported."""
        extractor = MusicFileExtractor()

        required_formats = {".aac", ".au", ".flac", ".mp3", ".ogg"}

        for fmt in required_formats:
            assert (
                fmt in extractor.SUPPORTED_EXTENSIONS
            ), f"Format {fmt} should be in SUPPORTED_EXTENSIONS"

    def test_extractor_with_custom_extensions(self):
        """Test extractor initialization with custom extensions."""
        extractor = MusicFileExtractor(include_extensions=[".mp3", ".flac"])

        assert ".mp3" in extractor.extensions
        assert ".flac" in extractor.extensions
        assert ".wav" not in extractor.extensions

    def test_extractor_with_invalid_extensions(self):
        """Test that invalid extensions are filtered out."""
        extractor = MusicFileExtractor(include_extensions=[".mp3", ".invalid"])

        assert ".mp3" in extractor.extensions
        assert ".invalid" not in extractor.extensions

    def test_find_music_files_nonexistent_directory(self):
        """Test that FileNotFoundError is raised for nonexistent directory."""
        extractor = MusicFileExtractor()

        with pytest.raises(FileNotFoundError):
            extractor.find_music_files("/nonexistent/directory")

    def test_find_music_files_not_a_directory(self, tmp_path):
        """Test that NotADirectoryError is raised when path is a file."""
        extractor = MusicFileExtractor()
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")

        with pytest.raises(NotADirectoryError):
            extractor.find_music_files(str(test_file))

    def test_find_music_files_empty_directory(self, tmp_path):
        """Test scanning an empty directory."""
        extractor = MusicFileExtractor()
        files = extractor.find_music_files(str(tmp_path))

        assert len(files) == 0

    def test_find_music_files_aac(self, tmp_path):
        """Test that AAC files are found."""
        extractor = MusicFileExtractor()

        # Create test AAC file
        aac_file = tmp_path / "test.aac"
        aac_file.touch()

        files = extractor.find_music_files(str(tmp_path))

        assert len(files) == 1
        assert files[0].suffix == ".aac"

    def test_find_music_files_au(self, tmp_path):
        """Test that AU files are found."""
        extractor = MusicFileExtractor()

        # Create test AU file
        au_file = tmp_path / "test.au"
        au_file.touch()

        files = extractor.find_music_files(str(tmp_path))

        assert len(files) == 1
        assert files[0].suffix == ".au"

    def test_find_music_files_flac(self, tmp_path):
        """Test that FLAC files are found."""
        extractor = MusicFileExtractor()

        # Create test FLAC file
        flac_file = tmp_path / "test.flac"
        flac_file.touch()

        files = extractor.find_music_files(str(tmp_path))

        assert len(files) == 1
        assert files[0].suffix == ".flac"

    def test_find_music_files_mp3(self, tmp_path):
        """Test that MP3 files are found."""
        extractor = MusicFileExtractor()

        # Create test MP3 file
        mp3_file = tmp_path / "test.mp3"
        mp3_file.touch()

        files = extractor.find_music_files(str(tmp_path))

        assert len(files) == 1
        assert files[0].suffix == ".mp3"

    def test_find_music_files_ogg(self, tmp_path):
        """Test that OGG files are found."""
        extractor = MusicFileExtractor()

        # Create test OGG file
        ogg_file = tmp_path / "test.ogg"
        ogg_file.touch()

        files = extractor.find_music_files(str(tmp_path))

        assert len(files) == 1
        assert files[0].suffix == ".ogg"

    def test_find_music_files_multiple_formats(self, tmp_path):
        """Test finding multiple audio formats."""
        extractor = MusicFileExtractor()

        # Create test files for all required formats
        (tmp_path / "test.aac").touch()
        (tmp_path / "test.au").touch()
        (tmp_path / "test.flac").touch()
        (tmp_path / "test.mp3").touch()
        (tmp_path / "test.ogg").touch()
        (tmp_path / "readme.txt").touch()  # Should be ignored

        files = extractor.find_music_files(str(tmp_path))

        assert len(files) == 5
        extensions = {f.suffix for f in files}
        assert extensions == {".aac", ".au", ".flac", ".mp3", ".ogg"}

    def test_find_music_files_recursive(self, tmp_path):
        """Test recursive directory scanning."""
        extractor = MusicFileExtractor()

        # Create nested directory structure
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        (tmp_path / "test1.mp3").touch()
        (subdir / "test2.mp3").touch()

        files = extractor.find_music_files(str(tmp_path), recursive=True)
        assert len(files) == 2

        files_non_recursive = extractor.find_music_files(str(tmp_path), recursive=False)
        assert len(files_non_recursive) == 1

    def test_find_music_files_case_insensitive(self, tmp_path):
        """Test that file extensions are matched case-insensitively."""
        extractor = MusicFileExtractor()

        (tmp_path / "test1.MP3").touch()
        (tmp_path / "test2.FLaC").touch()
        (tmp_path / "test3.OGG").touch()

        files = extractor.find_music_files(str(tmp_path))

        assert len(files) == 3

    def test_parse_filename_with_separator(self):
        """Test parsing filename with artist - title format."""
        artist, title = MusicFileExtractor._parse_filename("Artist Name - Song Title")

        assert artist == "Artist Name"
        assert title == "Song Title"

    def test_parse_filename_without_separator(self):
        """Test parsing filename without separator."""
        artist, title = MusicFileExtractor._parse_filename("SongTitle")

        assert artist is None
        assert title is None

    def test_parse_filename_multiple_separators(self):
        """Test parsing filename with multiple separators."""
        artist, title = MusicFileExtractor._parse_filename("Artist - Song - Part 1")

        assert artist == "Artist"
        assert title == "Song - Part 1"

    def test_safe_get_first_with_valid_key(self):
        """Test _safe_get_first with valid audio tags."""
        mock_audio = {"artist": ["Test Artist"], "album": ["Test Album"]}

        result = MusicFileExtractor._safe_get_first(mock_audio, ["artist"])
        assert result == "Test Artist"

    def test_safe_get_first_with_multiple_keys(self):
        """Test _safe_get_first with multiple keys."""
        mock_audio = {"albumartist": ["Album Artist"]}

        result = MusicFileExtractor._safe_get_first(
            mock_audio, ["artist", "albumartist"]
        )
        assert result == "Album Artist"

    def test_safe_get_first_with_empty_value(self):
        """Test _safe_get_first with empty values."""
        mock_audio = {"artist": ["  "], "album": ["Test Album"]}

        result = MusicFileExtractor._safe_get_first(mock_audio, ["artist"])
        assert result is None

    def test_safe_get_first_missing_key(self):
        """Test _safe_get_first with missing key."""
        mock_audio = {"album": ["Test Album"]}

        result = MusicFileExtractor._safe_get_first(mock_audio, ["artist"])
        assert result is None

    def test_extract_all_with_errors(self, tmp_path, caplog):
        """Test that extract_all continues after errors."""
        extractor = MusicFileExtractor()

        # Create some empty files (will fail metadata extraction)
        (tmp_path / "test1.mp3").touch()
        (tmp_path / "test2.mp3").touch()

        # Should not raise exception, just log warnings
        metadata_list = extractor.extract_all(str(tmp_path))

        # Files without proper metadata should be skipped
        assert "Skipping file" in caplog.text or len(metadata_list) == 0
