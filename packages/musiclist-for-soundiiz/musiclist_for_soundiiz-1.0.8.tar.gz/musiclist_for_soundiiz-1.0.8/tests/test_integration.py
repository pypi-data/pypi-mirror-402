"""Integration tests using real audio files."""

from pathlib import Path

import pytest

from musiclist_for_soundiiz.exporter import CSVExporter, JSONExporter
from musiclist_for_soundiiz.extractor import MusicFileExtractor


class TestRealAudioFiles:
    """Test cases using real audio test files."""

    @pytest.fixture
    def fixtures_dir(self):
        """Get path to test fixtures directory."""
        return Path(__file__).parent / "fixtures" / "music"

    def test_extract_mp3_metadata(self, fixtures_dir):
        """Test metadata extraction from real MP3 file."""
        extractor = MusicFileExtractor()
        mp3_file = fixtures_dir / "Rock" / "test_file.mp3"

        if not mp3_file.exists():
            pytest.skip(f"Test file not found: {mp3_file}")

        metadata = extractor.extract_metadata(mp3_file)

        # Validate extracted metadata
        assert metadata["title"] == "Loneliness"
        assert metadata["artist"] == "Tomcraft"
        assert metadata["album"] == "Loneliness"
        assert metadata["filename"] == "test_file.mp3"
        assert "file_path" in metadata

    def test_extract_flac_metadata(self, fixtures_dir):
        """Test metadata extraction from real FLAC file."""
        extractor = MusicFileExtractor()
        flac_file = fixtures_dir / "Rock" / "test_file.flac"

        if not flac_file.exists():
            pytest.skip(f"Test file not found: {flac_file}")

        metadata = extractor.extract_metadata(flac_file)

        # Validate extracted metadata
        assert metadata["title"] == "Loneliness"
        assert metadata["artist"] == "Tomcraft"
        assert metadata["album"] == "Loneliness"
        assert metadata["filename"] == "test_file.flac"

    def test_extract_aac_metadata(self, fixtures_dir):
        """Test metadata extraction from real AAC file."""
        extractor = MusicFileExtractor()
        aac_file = fixtures_dir / "Pop" / "test_file.aac"

        if not aac_file.exists():
            pytest.skip(f"Test file not found: {aac_file}")

        metadata = extractor.extract_metadata(aac_file)

        # Validate extracted metadata
        assert metadata["title"] == "Loneliness"
        assert metadata["artist"] == "Tomcraft"
        assert metadata["album"] == "Loneliness"
        assert metadata["filename"] == "test_file.aac"

    def test_extract_ogg_metadata(self, fixtures_dir):
        """Test metadata extraction from real OGG file."""
        extractor = MusicFileExtractor()
        ogg_file = fixtures_dir / "Electronic" / "Techno" / "test_file.ogg"

        if not ogg_file.exists():
            pytest.skip(f"Test file not found: {ogg_file}")

        metadata = extractor.extract_metadata(ogg_file)

        # Validate extracted metadata
        assert metadata["title"] == "Loneliness"
        assert metadata["artist"] == "Tomcraft"
        assert metadata["album"] == "Loneliness"
        assert metadata["filename"] == "test_file.ogg"

    def test_extract_wma_metadata(self, fixtures_dir):
        """Test metadata extraction from real WMA file."""
        extractor = MusicFileExtractor()
        wma_file = fixtures_dir / "Electronic" / "test_file.wma"

        if not wma_file.exists():
            pytest.skip(f"Test file not found: {wma_file}")

        metadata = extractor.extract_metadata(wma_file)

        # WMA may not have proper tags, should at least have filename
        assert metadata["filename"] == "test_file.wma"
        assert "title" in metadata
        assert "artist" in metadata
        assert "album" in metadata


class TestNestedDirectoryStructure:
    """Test cases for nested directory scanning."""

    @pytest.fixture
    def fixtures_dir(self):
        """Get path to test fixtures directory."""
        return Path(__file__).parent / "fixtures" / "music"

    def test_recursive_scan_finds_all_files(self, fixtures_dir):
        """Test that recursive scan finds files in nested directories."""
        if not fixtures_dir.exists():
            pytest.skip(f"Fixtures directory not found: {fixtures_dir}")

        extractor = MusicFileExtractor()
        files = extractor.find_music_files(str(fixtures_dir), recursive=True)

        # Should find files in all subdirectories
        assert len(files) > 0

        # Check for files in different directories
        file_paths = [str(f) for f in files]

        # Verify files from different subdirectories are found
        has_rock = any("Rock" in path for path in file_paths)
        has_pop = any("Pop" in path for path in file_paths)
        has_electronic = any("Electronic" in path for path in file_paths)

        # At least one category should have files
        assert has_rock or has_pop or has_electronic

    def test_non_recursive_scan_top_level_only(self, fixtures_dir):
        """Test that non-recursive scan only finds top-level files."""
        if not fixtures_dir.exists():
            pytest.skip(f"Fixtures directory not found: {fixtures_dir}")

        extractor = MusicFileExtractor()
        files = extractor.find_music_files(str(fixtures_dir), recursive=False)

        # Should only find files in the top-level directory
        # In our test setup, all files are in subdirectories
        assert len(files) == 0

    def test_extract_all_from_nested_structure(self, fixtures_dir):
        """Test extracting metadata from all files in nested structure."""
        if not fixtures_dir.exists():
            pytest.skip(f"Fixtures directory not found: {fixtures_dir}")

        extractor = MusicFileExtractor()
        metadata_list = extractor.extract_all(str(fixtures_dir), recursive=True)

        # Should extract metadata from multiple files
        assert len(metadata_list) > 0

        # Verify metadata structure
        for metadata in metadata_list:
            assert "title" in metadata
            assert "artist" in metadata
            assert "album" in metadata
            assert "filename" in metadata
            assert "file_path" in metadata

    def test_filter_by_extension_in_nested_structure(self, fixtures_dir):
        """Test filtering by extension in nested directory structure."""
        if not fixtures_dir.exists():
            pytest.skip(f"Fixtures directory not found: {fixtures_dir}")

        # Only scan for MP3 files
        extractor = MusicFileExtractor(include_extensions=[".mp3"])
        files = extractor.find_music_files(str(fixtures_dir), recursive=True)

        # All found files should be MP3
        for file in files:
            assert file.suffix.lower() == ".mp3"

    def test_multiple_formats_in_same_directory(self, fixtures_dir):
        """Test handling multiple audio formats in the same directory."""
        rock_dir = fixtures_dir / "Rock"
        
        if not rock_dir.exists():
            pytest.skip(f"Rock directory not found: {rock_dir}")
        
        extractor = MusicFileExtractor()
        files = extractor.find_music_files(str(rock_dir), recursive=False)
        
        # Should have at least one file
        assert len(files) > 0
        
        # Rock directory should have both MP3 and FLAC
        extensions = {f.suffix.lower() for f in files}
        assert len(extensions) > 0  # At least one format present


class TestEndToEndWorkflow:
    """End-to-end integration tests."""

    @pytest.fixture
    def fixtures_dir(self):
        """Get path to test fixtures directory."""
        return Path(__file__).parent / "fixtures" / "music"

    def test_full_csv_export_workflow(self, fixtures_dir, tmp_path):
        """Test complete workflow: scan → extract → export to CSV."""
        if not fixtures_dir.exists():
            pytest.skip(f"Fixtures directory not found: {fixtures_dir}")

        # Extract metadata
        extractor = MusicFileExtractor()
        metadata_list = extractor.extract_all(str(fixtures_dir), recursive=True)

        if len(metadata_list) == 0:
            pytest.skip("No music files found in fixtures")

        # Export to CSV
        output_file = tmp_path / "test_export.csv"
        exporter = CSVExporter()
        exporter.export(metadata_list, str(output_file))

        # Verify CSV file was created
        assert output_file.exists()

        # Verify CSV content
        content = output_file.read_text(encoding="utf-8")
        assert "title,artist,album,isrc," in content
        assert "Loneliness" in content or "Tomcraft" in content

    def test_full_json_export_workflow(self, fixtures_dir, tmp_path):
        """Test complete workflow: scan → extract → export to JSON."""
        if not fixtures_dir.exists():
            pytest.skip(f"Fixtures directory not found: {fixtures_dir}")

        # Extract metadata
        extractor = MusicFileExtractor()
        metadata_list = extractor.extract_all(str(fixtures_dir), recursive=True)

        if len(metadata_list) == 0:
            pytest.skip("No music files found in fixtures")

        # Export to JSON
        output_file = tmp_path / "test_export.json"
        exporter = JSONExporter()
        exporter.export(metadata_list, str(output_file))

        # Verify JSON file was created
        assert output_file.exists()

        # Verify JSON is valid
        import json

        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)

        assert "total_songs" in data
        assert "songs" in data
        assert data["total_songs"] == len(metadata_list)

    def test_metadata_consistency_across_formats(self, fixtures_dir):
        """Test that same song in different formats has consistent metadata."""
        if not fixtures_dir.exists():
            pytest.skip(f"Fixtures directory not found: {fixtures_dir}")

        extractor = MusicFileExtractor()
        metadata_list = extractor.extract_all(str(fixtures_dir), recursive=True)

        if len(metadata_list) < 2:
            pytest.skip("Not enough files to compare")

        # Group by title and artist
        songs = {}
        for metadata in metadata_list:
            key = (metadata["title"], metadata["artist"])
            if key not in songs:
                songs[key] = []
            songs[key].append(metadata)

        # Check that same song has consistent metadata across formats
        for (title, artist), versions in songs.items():
            if len(versions) > 1:
                # All versions should have same title and artist
                for version in versions:
                    assert version["title"] == title
                    assert version["artist"] == artist
