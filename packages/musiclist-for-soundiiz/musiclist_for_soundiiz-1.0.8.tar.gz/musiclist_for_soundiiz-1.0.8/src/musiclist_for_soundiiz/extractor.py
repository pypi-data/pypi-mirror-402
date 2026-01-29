"""Music file metadata extraction."""

import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from mutagen import File as MutagenFile

logger = logging.getLogger(__name__)


class MusicFileExtractor:
    """Extract metadata from music files."""

    # Soundiiz supported audio formats
    SUPPORTED_EXTENSIONS = {
        ".aac",  # AAC Audio File
        ".au",  # AU Audio File
        ".flac",  # FLAC Audio File
        ".mp3",  # MP3 Audio File
        ".ogg",  # OGG Vorbis File
        ".m4a",  # MPEG-4 Audio
        ".wav",  # WAV Audio File
        ".wma",  # Windows Media Audio
    }

    def __init__(self, include_extensions: Optional[List[str]] = None):
        """
        Initialize the extractor.

        Args:
            include_extensions: List of file extensions to include (e.g., ['.mp3', '.flac']).
                               If None, all supported extensions are used.
        """
        if include_extensions:
            self.extensions = {ext.lower() for ext in include_extensions}
            # Validate extensions
            invalid_exts = self.extensions - self.SUPPORTED_EXTENSIONS
            if invalid_exts:
                logger.warning(
                    f"Unsupported extensions will be ignored: {invalid_exts}"
                )
                self.extensions = self.extensions & self.SUPPORTED_EXTENSIONS
        else:
            self.extensions = self.SUPPORTED_EXTENSIONS

    def find_music_files(self, directory: str, recursive: bool = True) -> List[Path]:
        """
        Find all supported music files in a directory.

        Args:
            directory: Path to the directory to scan
            recursive: Whether to search subdirectories recursively

        Returns:
            List of Path objects for found music files

        Raises:
            FileNotFoundError: If directory doesn't exist
            PermissionError: If directory is not accessible
        """
        dir_path = Path(directory)

        if not dir_path.exists():
            raise FileNotFoundError(f"Directory not found: {directory}")

        if not dir_path.is_dir():
            raise NotADirectoryError(f"Not a directory: {directory}")

        music_files = []

        try:
            if recursive:
                pattern = "**/*"
            else:
                pattern = "*"

            for file_path in dir_path.glob(pattern):
                # Skip macOS resource fork files and hidden files
                if file_path.name.startswith('._') or file_path.name.startswith('.'):
                    logger.debug(f"Skipping hidden/system file: {file_path}")
                    continue
                    
                if file_path.is_file() and file_path.suffix.lower() in self.extensions:
                    music_files.append(file_path)
                    logger.debug(f"Found music file: {file_path}")

        except PermissionError as e:
            logger.error(f"Permission denied accessing directory: {e}")
            raise

        logger.info(f"Found {len(music_files)} music files in {directory}")
        return sorted(music_files)

    def extract_metadata(self, file_path: Path) -> Dict[str, str]:
        """
        Extract metadata from a music file.

        Args:
            file_path: Path to the music file

        Returns:
            Dictionary with keys: title, artist, album, isrc, genre, year, duration

        Raises:
            ValueError: If file cannot be read or is not a supported format
        """
        try:
            audio = MutagenFile(str(file_path), easy=True)

            if audio is None:
                raise ValueError(f"Cannot read file or unsupported format: {file_path}")

            # Extract metadata from tags
            title_meta = self._safe_get_first(audio, ["title"])
            artist_meta = self._safe_get_first(
                audio, ["artist", "albumartist", "performer"]
            )
            album_meta = self._safe_get_first(audio, ["album"])
            isrc_meta = self._safe_get_first(audio, ["isrc"])
            genre_meta = self._safe_get_first(audio, ["genre"])
            year_meta = self._safe_get_first(audio, ["date", "year"])

            # Try to parse filename for artist and title (format: "Artist - Title")
            basename = file_path.stem
            artist_file, title_file = self._parse_filename(basename)

            # Prefer filename parsing over metadata for artist and title
            artist = artist_file or artist_meta or "Unknown Artist"
            title = title_file or title_meta or basename
            album = album_meta or "Unknown Album"
            isrc = isrc_meta or ""
            genre = genre_meta or ""
            year = year_meta or ""

            # Get duration if available
            duration = ""
            if hasattr(audio.info, "length"):
                duration = str(int(audio.info.length))

            logger.debug(
                f"Extracted metadata from {file_path.name}: "
                f"Title='{title}', Artist='{artist}', Album='{album}'"
            )

            return {
                "title": title,
                "artist": artist,
                "album": album,
                "isrc": isrc,
                "genre": genre,
                "year": year,
                "duration": duration,
                "file_path": str(file_path),
                "filename": file_path.name,
            }

        except Exception as e:
            logger.error(f"Error extracting metadata from {file_path}: {e}")
            raise ValueError(f"Failed to extract metadata: {e}") from e

    def extract_all(
        self, directory: str, recursive: bool = True
    ) -> List[Dict[str, str]]:
        """
        Find and extract metadata from all music files in a directory.

        Args:
            directory: Path to the directory to scan
            recursive: Whether to search subdirectories recursively

        Returns:
            List of metadata dictionaries
        """
        music_files = self.find_music_files(directory, recursive)
        metadata_list = []

        for file_path in music_files:
            try:
                metadata = self.extract_metadata(file_path)
                metadata_list.append(metadata)
            except Exception as e:
                logger.warning(f"Skipping file {file_path}: {e}")
                continue

        logger.info(f"Successfully extracted metadata from {len(metadata_list)} files")
        return metadata_list

    @staticmethod
    def _safe_get_first(audio, keys: List[str]) -> Optional[str]:
        """
        Get first non-empty value from audio tags.

        Args:
            audio: Mutagen audio object
            keys: List of tag keys to try

        Returns:
            First non-empty string value or None
        """
        for key in keys:
            if key in audio and audio[key]:
                value = audio[key][0]
                if isinstance(value, bytes):
                    value = value.decode("utf-8", errors="ignore")
                value_stripped = value.strip()
                if value_stripped:
                    return value_stripped
        return None

    @staticmethod
    def _parse_filename(basename: str) -> Tuple[Optional[str], Optional[str]]:
        """
        Parse filename in format "Artist - Title".

        Args:
            basename: Filename without extension

        Returns:
            Tuple of (artist, title) or (None, basename) if parsing fails
        """
        if " - " in basename:
            parts = basename.split(" - ", 1)
            if len(parts) == 2:
                artist = parts[0].strip()
                title = parts[1].strip()
                if artist and title:
                    return artist, title

        return None, None
