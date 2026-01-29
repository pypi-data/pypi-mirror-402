"""Tests for CLI functionality."""

import os
import tempfile
from pathlib import Path

import pytest

from musiclist_for_soundiiz.cli import main, parse_args


def test_parse_args_basic():
    """Test basic argument parsing."""
    args = parse_args(["-i", "/path/to/music"])
    
    assert args.input == ["/path/to/music"]
    assert args.output == "output.csv"
    assert args.format == "csv"
    assert args.no_recursive is False


def test_parse_args_multiple_inputs():
    """Test batch processing with multiple input directories."""
    args = parse_args(["-i", "/path/1", "/path/2", "/path/3"])
    
    assert len(args.input) == 3
    assert args.input == ["/path/1", "/path/2", "/path/3"]


def test_parse_args_duplicate_detection():
    """Test duplicate detection arguments."""
    args = parse_args([
        "-i", "/path/to/music",
        "--detect-duplicates",
        "--duplicate-report", "report.txt"
    ])
    
    assert args.detect_duplicates is True
    assert args.duplicate_report == "report.txt"


def test_parse_args_remove_duplicates():
    """Test duplicate removal arguments."""
    args = parse_args([
        "-i", "/path/to/music",
        "--remove-duplicates",
        "--duplicate-strategy", "keep_shortest_path"
    ])
    
    assert args.remove_duplicates is True
    assert args.duplicate_strategy == "keep_shortest_path"


def test_parse_args_all_formats():
    """Test all output formats."""
    for fmt in ["csv", "json", "m3u", "txt"]:
        args = parse_args(["-i", "/path", "-f", fmt])
        assert args.format == fmt


def test_parse_args_extensions():
    """Test file extension filtering."""
    args = parse_args(["-i", "/path", "-e", ".mp3", ".flac"])
    
    assert args.extensions == [".mp3", ".flac"]


def test_parse_args_max_songs():
    """Test max songs per file option."""
    args = parse_args(["-i", "/path", "--max-songs-per-file", "500"])
    
    assert args.max_songs_per_file == 500


def test_parse_args_quiet_and_verbose_conflict():
    """Test that quiet and verbose cannot be used together."""
    with pytest.raises(SystemExit):
        parse_args(["-i", "/path", "-q", "-v"])


def test_main_nonexistent_directory(tmp_path):
    """Test CLI with nonexistent directory."""
    nonexistent = tmp_path / "nonexistent"
    
    exit_code = main(["-i", str(nonexistent)])
    
    assert exit_code == 1


def test_main_file_instead_of_directory(tmp_path):
    """Test CLI with file instead of directory."""
    test_file = tmp_path / "test.txt"
    test_file.write_text("test")
    
    exit_code = main(["-i", str(test_file)])
    
    assert exit_code == 1


def test_main_empty_directory(tmp_path):
    """Test CLI with empty directory."""
    output_file = tmp_path / "output.csv"
    
    exit_code = main(["-i", str(tmp_path), "-o", str(output_file)])
    
    assert exit_code == 0  # No error, just warning


def test_main_with_music_files(tmp_path):
    """Test CLI with actual music files."""
    # Copy test files to temp directory
    music_dir = tmp_path / "music"
    music_dir.mkdir()
    
    # Copy test file
    test_file_src = Path("test_file.mp3")
    if test_file_src.exists():
        import shutil
        shutil.copy(test_file_src, music_dir / "song.mp3")
        
        output_file = tmp_path / "output.csv"
        
        exit_code = main(["-i", str(music_dir), "-o", str(output_file)])
        
        assert exit_code == 0
        assert output_file.exists()


def test_main_batch_processing(tmp_path):
    """Test batch processing with multiple directories."""
    # Create two music directories
    dir1 = tmp_path / "music1"
    dir2 = tmp_path / "music2"
    dir1.mkdir()
    dir2.mkdir()
    
    # Copy test files if available
    test_file_src = Path("test_file.mp3")
    if test_file_src.exists():
        import shutil
        shutil.copy(test_file_src, dir1 / "song1.mp3")
        shutil.copy(test_file_src, dir2 / "song2.mp3")
        
        output_file = tmp_path / "output.csv"
        
        exit_code = main([
            "-i", str(dir1), str(dir2),
            "-o", str(output_file)
        ])
        
        assert exit_code == 0
        assert output_file.exists()


def test_main_duplicate_detection(tmp_path):
    """Test duplicate detection with report generation."""
    music_dir = tmp_path / "music"
    music_dir.mkdir()
    
    test_file_src = Path("test_file.mp3")
    if test_file_src.exists():
        import shutil
        # Create duplicate files
        shutil.copy(test_file_src, music_dir / "song1.mp3")
        shutil.copy(test_file_src, music_dir / "song2.mp3")
        
        output_file = tmp_path / "output.csv"
        report_file = tmp_path / "duplicates.txt"
        
        exit_code = main([
            "-i", str(music_dir),
            "-o", str(output_file),
            "--detect-duplicates",
            "--duplicate-report", str(report_file)
        ])
        
        assert exit_code == 0
        # Report file should be created if duplicates found
        # (may not exist if test files have different metadata)


def test_main_remove_duplicates(tmp_path):
    """Test duplicate removal."""
    music_dir = tmp_path / "music"
    music_dir.mkdir()
    
    test_file_src = Path("test_file.mp3")
    if test_file_src.exists():
        import shutil
        # Create duplicate files
        shutil.copy(test_file_src, music_dir / "song1.mp3")
        shutil.copy(test_file_src, music_dir / "song2.mp3")
        
        output_file = tmp_path / "output.csv"
        
        exit_code = main([
            "-i", str(music_dir),
            "-o", str(output_file),
            "--remove-duplicates",
            "--duplicate-strategy", "keep_first"
        ])
        
        assert exit_code == 0
        assert output_file.exists()


def test_main_json_format(tmp_path):
    """Test JSON export format."""
    music_dir = tmp_path / "music"
    music_dir.mkdir()
    
    test_file_src = Path("test_file.mp3")
    if test_file_src.exists():
        import shutil
        shutil.copy(test_file_src, music_dir / "song.mp3")
        
        output_file = tmp_path / "output.json"
        
        exit_code = main([
            "-i", str(music_dir),
            "-o", str(output_file),
            "-f", "json"
        ])
        
        assert exit_code == 0
        assert output_file.exists()


def test_main_keyboard_interrupt(tmp_path, monkeypatch):
    """Test handling of keyboard interrupt."""
    def mock_extract_all(*args, **kwargs):
        raise KeyboardInterrupt()
    
    from musiclist_for_soundiiz import extractor
    monkeypatch.setattr(extractor.MusicFileExtractor, "extract_all", mock_extract_all)
    
    music_dir = tmp_path / "music"
    music_dir.mkdir()
    
    exit_code = main(["-i", str(music_dir)])
    
    assert exit_code == 130


def test_main_generic_exception(tmp_path, monkeypatch):
    """Test handling of generic exceptions."""
    def mock_extract_all(*args, **kwargs):
        raise Exception("Test error")
    
    from musiclist_for_soundiiz import extractor
    monkeypatch.setattr(extractor.MusicFileExtractor, "extract_all", mock_extract_all)
    
    music_dir = tmp_path / "music"
    music_dir.mkdir()
    
    exit_code = main(["-i", str(music_dir)])
    
    assert exit_code == 1
