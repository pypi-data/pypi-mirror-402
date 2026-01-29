"""Tests for duplicate detection functionality."""

import pytest

from musiclist_for_soundiiz.duplicate_detector import DuplicateDetector


@pytest.fixture
def sample_metadata():
    """Sample metadata with duplicates."""
    return [
        {
            "title": "Song A",
            "artist": "Artist 1",
            "album": "Album 1",
            "file_path": "/music/song_a_1.mp3",
        },
        {
            "title": "Song A",
            "artist": "Artist 1",
            "album": "Album 1",
            "file_path": "/music/duplicate/song_a_2.mp3",
        },
        {
            "title": "Song B",
            "artist": "Artist 2",
            "album": "Album 2",
            "file_path": "/music/song_b.mp3",
        },
        {
            "title": "Song A",
            "artist": "Artist 1",
            "album": "Album 2",
            "file_path": "/music/another/song_a_3.mp3",
        },
        {
            "title": "Song C",
            "artist": "Artist 3",
            "album": "Album 3",
            "file_path": "/music/song_c.mp3",
        },
    ]


def test_find_duplicates_basic(sample_metadata):
    """Test basic duplicate detection."""
    detector = DuplicateDetector()
    duplicates = detector.find_duplicates(sample_metadata)

    # Should find one duplicate group (Song A by Artist 1)
    assert len(duplicates) == 1
    
    # Get the duplicate entries
    dup_entries = list(duplicates.values())[0]
    assert len(dup_entries) == 3  # Three copies of Song A


def test_find_duplicates_case_insensitive(sample_metadata):
    """Test case-insensitive duplicate detection."""
    # Add case variation
    metadata_with_case = sample_metadata + [
        {
            "title": "song a",  # lowercase
            "artist": "ARTIST 1",  # uppercase
            "album": "Album X",
            "file_path": "/music/song_a_case.mp3",
        }
    ]
    
    detector = DuplicateDetector(case_sensitive=False)
    duplicates = detector.find_duplicates(metadata_with_case)
    
    # Should find the case variation as duplicate
    dup_entries = list(duplicates.values())[0]
    assert len(dup_entries) == 4


def test_find_duplicates_case_sensitive(sample_metadata):
    """Test case-sensitive duplicate detection."""
    metadata_with_case = sample_metadata + [
        {
            "title": "song a",  # lowercase
            "artist": "ARTIST 1", # uppercase
            "album": "Album X",
            "file_path": "/music/song_a_case.mp3",
        }
    ]
    
    detector = DuplicateDetector(case_sensitive=True)
    duplicates = detector.find_duplicates(metadata_with_case)
    
    # Should NOT find case variation as duplicate
    dup_entries = list(duplicates.values())[0]
    assert len(dup_entries) == 3  # Only exact matches


def test_no_duplicates():
    """Test when there are no duplicates."""
    metadata = [
        {"title": "Song A", "artist": "Artist 1", "file_path": "/music/a.mp3"},
        {"title": "Song B", "artist": "Artist 2", "file_path": "/music/b.mp3"},
        {"title": "Song C", "artist": "Artist 3", "file_path": "/music/c.mp3"},
    ]
    
    detector = DuplicateDetector()
    duplicates = detector.find_duplicates(metadata)
    
    assert len(duplicates) == 0


def test_remove_duplicates_keep_first(sample_metadata):
    """Test removing duplicates keeping first occurrence."""
    detector = DuplicateDetector()
    unique_list, removed_list = detector.remove_duplicates(
        sample_metadata, strategy="keep_first"
    )
    
    # Should keep 3 unique songs
    assert len(unique_list) == 3
    # Should remove 2 duplicates
    assert len(removed_list) == 2
    
    # First occurrence should be kept
    kept_paths = [m["file_path"] for m in unique_list]
    assert "/music/song_a_1.mp3" in kept_paths
    assert "/music/duplicate/song_a_2.mp3" not in kept_paths


def test_remove_duplicates_keep_last(sample_metadata):
    """Test removing duplicates keeping last occurrence."""
    detector = DuplicateDetector()
    unique_list, removed_list = detector.remove_duplicates(
        sample_metadata, strategy="keep_last"
    )
    
    # Should keep 3 unique songs
    assert len(unique_list) == 3
    # Should remove 2 duplicates
    assert len(removed_list) == 2
    
    # Last occurrence should be kept
    kept_paths = [m["file_path"] for m in unique_list]
    assert "/music/another/song_a_3.mp3" in kept_paths
    assert "/music/song_a_1.mp3" not in kept_paths


def test_remove_duplicates_keep_shortest_path(sample_metadata):
    """Test removing duplicates keeping shortest path."""
    detector = DuplicateDetector()
    unique_list, removed_list = detector.remove_duplicates(
        sample_metadata, strategy="keep_shortest_path"
    )
    
    # Should keep 3 unique songs
    assert len(unique_list) == 3
    # Should remove 2 duplicates
    assert len(removed_list) == 2
    
    # Shortest path should be kept
    kept_paths = [m["file_path"] for m in unique_list]
    assert "/music/song_a_1.mp3" in kept_paths  # Shortest
    assert "/music/duplicate/song_a_2.mp3" not in kept_paths


def test_remove_duplicates_invalid_strategy(sample_metadata):
    """Test invalid removal strategy."""
    detector = DuplicateDetector()
    
    with pytest.raises(ValueError, match="Unknown strategy"):
        detector.remove_duplicates(sample_metadata, strategy="invalid_strategy")


def test_get_duplicate_report_with_duplicates(sample_metadata):
    """Test duplicate report generation."""
    detector = DuplicateDetector()
    report = detector.get_duplicate_report(sample_metadata)
    
    assert "Song A" in report
    assert "Artist 1" in report
    assert "1 duplicate song groups" in report
    assert "/music/song_a_1.mp3" in report


def test_get_duplicate_report_no_duplicates():
    """Test duplicate report when no duplicates exist."""
    metadata = [
        {"title": "Song A", "artist": "Artist 1", "file_path": "/music/a.mp3"},
        {"title": "Song B", "artist": "Artist 2", "file_path": "/music/b.mp3"},
    ]
    
    detector = DuplicateDetector()
    report = detector.get_duplicate_report(metadata)
    
    assert "No duplicates found" in report


def test_skip_entries_without_title_or_artist():
    """Test that entries without title or artist are skipped."""
    metadata = [
        {"title": "", "artist": "Artist 1", "file_path": "/music/a.mp3"},
        {"title": "Song B", "artist": "", "file_path": "/music/b.mp3"},
        {"title": "Song C", "artist": "Artist 3", "file_path": "/music/c.mp3"},
    ]
    
    detector = DuplicateDetector()
    duplicates = detector.find_duplicates(metadata)
    
    # No duplicates should be found (entries without title/artist are skipped)
    assert len(duplicates) == 0
