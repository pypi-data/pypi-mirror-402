"""Export music metadata to various formats."""

import json
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List

logger = logging.getLogger(__name__)


class BaseExporter(ABC):
    """Base class for metadata exporters."""

    @abstractmethod
    def export(self, metadata_list: List[Dict[str, str]], output_path: str) -> None:
        """
        Export metadata to a file.

        Args:
            metadata_list: List of metadata dictionaries
            output_path: Path to the output file
        """
        pass


class CSVExporter(BaseExporter):
    """Export metadata to CSV format compatible with Soundiiz."""

    def __init__(self, max_songs_per_file: int = 500):
        """
        Initialize CSV exporter.

        Args:
            max_songs_per_file: Maximum number of songs per CSV file.
                               If exceeded, multiple files will be created.
        """
        self.max_songs_per_file = max_songs_per_file

    def export(self, metadata_list: List[Dict[str, str]], output_path: str) -> None:
        """
        Export metadata to CSV file(s) in Soundiiz format.

        Soundiiz CSV format: title,artist,album,isrc,
        Note: The trailing comma is intentional per Soundiiz specification.

        Args:
            metadata_list: List of metadata dictionaries
            output_path: Base path for output file(s)
        """
        if not metadata_list:
            logger.warning("No metadata to export")
            return

        output_path_obj = Path(output_path)
        base_name = output_path_obj.stem
        extension = output_path_obj.suffix or ".csv"
        output_dir = output_path_obj.parent

        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # Split into multiple files if necessary
        total_files = (
            len(metadata_list) + self.max_songs_per_file - 1
        ) // self.max_songs_per_file

        for file_index in range(total_files):
            start_idx = file_index * self.max_songs_per_file
            end_idx = min(start_idx + self.max_songs_per_file, len(metadata_list))
            chunk = metadata_list[start_idx:end_idx]

            # Generate filename
            if total_files > 1:
                filename = f"{base_name}_{file_index + 1}{extension}"
            else:
                filename = f"{base_name}{extension}"

            file_path = output_dir / filename

            # Write CSV file
            with open(file_path, "w", encoding="utf-8", newline="") as csvfile:
                # Soundiiz CSV header with trailing comma
                csvfile.write("title,artist,album,isrc,\n")

                for metadata in chunk:
                    title = self._escape_csv(metadata["title"])
                    artist = self._escape_csv(metadata["artist"])
                    album = self._escape_csv(metadata["album"])
                    isrc = self._escape_csv(metadata.get("isrc", ""))

                    # Write row with trailing comma
                    csvfile.write(f"{title},{artist},{album},{isrc},\n")

            logger.info(
                f"Exported {len(chunk)} songs to {file_path} "
                f"(file {file_index + 1}/{total_files})"
            )

    @staticmethod
    def _escape_csv(text: str) -> str:
        """
        Escape CSV values according to RFC 4180.

        If the text contains commas or quotes, wrap it in quotes
        and double any internal quotes.

        Args:
            text: Text to escape

        Returns:
            Escaped text
        """
        if any(c in text for c in ['"', ","]):
            text = text.replace('"', '""')
            return f'"{text}"'
        return text


class JSONExporter(BaseExporter):
    """Export metadata to JSON format."""

    def __init__(self, pretty: bool = True, max_songs_per_file: int = 500):
        """
        Initialize JSON exporter.

        Args:
            pretty: Whether to format JSON with indentation
            max_songs_per_file: Maximum number of songs per JSON file
        """
        self.pretty = pretty
        self.max_songs_per_file = max_songs_per_file

    def export(self, metadata_list: List[Dict[str, str]], output_path: str) -> None:
        """
        Export metadata to JSON file(s).

        Args:
            metadata_list: List of metadata dictionaries
            output_path: Base path for output file(s)
        """
        if not metadata_list:
            logger.warning("No metadata to export")
            return

        output_path_obj = Path(output_path)
        base_name = output_path_obj.stem
        extension = output_path_obj.suffix or ".json"
        output_dir = output_path_obj.parent

        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # Split into multiple files if necessary
        total_files = (
            len(metadata_list) + self.max_songs_per_file - 1
        ) // self.max_songs_per_file

        for file_index in range(total_files):
            start_idx = file_index * self.max_songs_per_file
            end_idx = min(start_idx + self.max_songs_per_file, len(metadata_list))
            chunk = metadata_list[start_idx:end_idx]

            # Generate filename
            if total_files > 1:
                filename = f"{base_name}_{file_index + 1}{extension}"
            else:
                filename = f"{base_name}{extension}"

            file_path = output_dir / filename

            export_data = {
                "total_songs": len(chunk),
                "songs": chunk,
            }

            with open(file_path, "w", encoding="utf-8") as jsonfile:
                if self.pretty:
                    json.dump(export_data, jsonfile, indent=2, ensure_ascii=False)
                else:
                    json.dump(export_data, jsonfile, ensure_ascii=False)

            logger.info(
                f"Exported {len(chunk)} songs to {file_path} "
                f"(file {file_index + 1}/{total_files})"
            )


class M3UExporter(BaseExporter):
    """Export metadata to M3U playlist format."""

    def __init__(self, extended: bool = True, max_songs_per_file: int = 500):
        """
        Initialize M3U exporter.

        Args:
            extended: Whether to use extended M3U format (M3U8) with metadata
            max_songs_per_file: Maximum number of songs per M3U file
        """
        self.extended = extended
        self.max_songs_per_file = max_songs_per_file

    def export(self, metadata_list: List[Dict[str, str]], output_path: str) -> None:
        """
        Export metadata to M3U playlist file(s).

        Args:
            metadata_list: List of metadata dictionaries
            output_path: Base path for output file(s)
        """
        if not metadata_list:
            logger.warning("No metadata to export")
            return

        output_path_obj = Path(output_path)
        base_name = output_path_obj.stem
        extension = output_path_obj.suffix or ".m3u"
        output_dir = output_path_obj.parent

        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # Split into multiple files if necessary
        total_files = (
            len(metadata_list) + self.max_songs_per_file - 1
        ) // self.max_songs_per_file

        for file_index in range(total_files):
            start_idx = file_index * self.max_songs_per_file
            end_idx = min(start_idx + self.max_songs_per_file, len(metadata_list))
            chunk = metadata_list[start_idx:end_idx]

            # Generate filename
            if total_files > 1:
                filename = f"{base_name}_{file_index + 1}{extension}"
            else:
                filename = f"{base_name}{extension}"

            file_path = output_dir / filename

            with open(file_path, "w", encoding="utf-8") as m3ufile:
                if self.extended:
                    m3ufile.write("#EXTM3U\n")

                for metadata in chunk:
                    if self.extended:
                        duration = metadata.get("duration", "-1")
                        artist = metadata["artist"]
                        title = metadata["title"]
                        m3ufile.write(f"#EXTINF:{duration},{artist} - {title}\n")

                    path = metadata.get("file_path", "")
                    m3ufile.write(f"{path}\n")

            logger.info(
                f"Exported {len(chunk)} songs to {file_path} "
                f"(file {file_index + 1}/{total_files})"
            )


class TXTExporter(BaseExporter):
    """Export metadata to simple text format."""

    def __init__(self, max_songs_per_file: int = 500):
        """
        Initialize TXT exporter.

        Args:
            max_songs_per_file: Maximum number of songs per TXT file
        """
        self.max_songs_per_file = max_songs_per_file

    def export(self, metadata_list: List[Dict[str, str]], output_path: str) -> None:
        """
        Export metadata to text file(s) (format: Title - Artist).

        Args:
            metadata_list: List of metadata dictionaries
            output_path: Base path for output file(s)
        """
        if not metadata_list:
            logger.warning("No metadata to export")
            return

        output_path_obj = Path(output_path)
        base_name = output_path_obj.stem
        extension = output_path_obj.suffix or ".txt"
        output_dir = output_path_obj.parent

        # Create output directory if it doesn't exist
        output_dir.mkdir(parents=True, exist_ok=True)

        # Split into multiple files if necessary
        total_files = (
            len(metadata_list) + self.max_songs_per_file - 1
        ) // self.max_songs_per_file

        for file_index in range(total_files):
            start_idx = file_index * self.max_songs_per_file
            end_idx = min(start_idx + self.max_songs_per_file, len(metadata_list))
            chunk = metadata_list[start_idx:end_idx]

            # Generate filename
            if total_files > 1:
                filename = f"{base_name}_{file_index + 1}{extension}"
            else:
                filename = f"{base_name}{extension}"

            file_path = output_dir / filename

            with open(file_path, "w", encoding="utf-8") as txtfile:
                for metadata in chunk:
                    title = metadata["title"]
                    artist = metadata["artist"]
                    txtfile.write(f"{title} - {artist}\n")

            logger.info(
                f"Exported {len(chunk)} songs to {file_path} "
                f"(file {file_index + 1}/{total_files})"
            )


def get_exporter(format_type: str, **kwargs) -> BaseExporter:
    """
    Get exporter instance for the specified format.

    Args:
        format_type: Export format (csv, json, m3u, txt)
        **kwargs: Additional arguments for the exporter

    Returns:
        Exporter instance

    Raises:
        ValueError: If format is not supported
    """
    format_type = format_type.lower()

    exporters = {
        "csv": CSVExporter,
        "json": JSONExporter,
        "m3u": M3UExporter,
        "txt": TXTExporter,
    }

    if format_type not in exporters:
        raise ValueError(
            f"Unsupported format: {format_type}. "
            f"Supported formats: {', '.join(exporters.keys())}"
        )

    return exporters[format_type](**kwargs)
