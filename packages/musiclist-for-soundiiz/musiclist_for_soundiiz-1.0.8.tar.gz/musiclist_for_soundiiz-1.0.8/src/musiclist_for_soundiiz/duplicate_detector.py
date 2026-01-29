"""Duplicate detection for music files."""

import logging
from typing import Dict, List, Set, Tuple

logger = logging.getLogger(__name__)


class DuplicateDetector:
    """Detect duplicate music files based on metadata."""

    def __init__(self, case_sensitive: bool = False):
        """
        Initialize the duplicate detector.

        Args:
            case_sensitive: Whether to perform case-sensitive comparison
        """
        self.case_sensitive = case_sensitive

    def _normalize_key(self, title: str, artist: str) -> str:
        """
        Create a normalized key for comparison.

        Args:
            title: Song title
            artist: Artist name

        Returns:
            Normalized key string
        """
        key = f"{title}|{artist}"
        if not self.case_sensitive:
            key = key.lower()
        return key.strip()

    def find_duplicates(
        self, metadata_list: List[Dict[str, str]]
    ) -> Dict[str, List[Dict[str, str]]]:
        """
        Find duplicate songs based on title and artist.

        Args:
            metadata_list: List of metadata dictionaries

        Returns:
            Dictionary mapping duplicate keys to lists of duplicate entries.
            Only includes entries that have duplicates (2 or more files).
        """
        # Build index of all songs
        song_index: Dict[str, List[Dict[str, str]]] = {}

        for metadata in metadata_list:
            title = metadata.get("title", "")
            artist = metadata.get("artist", "")

            # Skip entries without title or artist
            if not title or not artist:
                continue

            key = self._normalize_key(title, artist)
            if key not in song_index:
                song_index[key] = []
            song_index[key].append(metadata)

        # Filter for actual duplicates (2+ entries)
        duplicates = {
            key: entries for key, entries in song_index.items() if len(entries) > 1
        }

        logger.info(
            f"Found {len(duplicates)} duplicate song groups "
            f"({sum(len(v) for v in duplicates.values())} total files)"
        )

        return duplicates

    def remove_duplicates(
        self, metadata_list: List[Dict[str, str]], strategy: str = "keep_first"
    ) -> Tuple[List[Dict[str, str]], List[Dict[str, str]]]:
        """
        Remove duplicates from metadata list.

        Args:
            metadata_list: List of metadata dictionaries
            strategy: Strategy for keeping files:
                - 'keep_first': Keep first occurrence
                - 'keep_last': Keep last occurrence
                - 'keep_shortest_path': Keep file with shortest path

        Returns:
            Tuple of (unique_list, removed_list)
        """
        duplicates = self.find_duplicates(metadata_list)

        # Create set of files to remove
        files_to_remove: Set[str] = set()

        for entries in duplicates.values():
            if strategy == "keep_first":
                # Remove all but first
                to_remove = entries[1:]
            elif strategy == "keep_last":
                # Remove all but last
                to_remove = entries[:-1]
            elif strategy == "keep_shortest_path":
                # Sort by path length and keep shortest
                sorted_entries = sorted(
                    entries, key=lambda x: len(x.get("file_path", ""))
                )
                to_remove = sorted_entries[1:]
            else:
                raise ValueError(f"Unknown strategy: {strategy}")

            for entry in to_remove:
                files_to_remove.add(entry.get("file_path", ""))

        # Split into unique and removed lists
        unique_list = [
            m for m in metadata_list if m.get("file_path", "") not in files_to_remove
        ]
        removed_list = [
            m for m in metadata_list if m.get("file_path", "") in files_to_remove
        ]

        logger.info(
            f"Removed {len(removed_list)} duplicate files using strategy '{strategy}'"
        )

        return unique_list, removed_list

    def get_duplicate_report(
        self, metadata_list: List[Dict[str, str]]
    ) -> str:
        """
        Generate a human-readable report of duplicates.

        Args:
            metadata_list: List of metadata dictionaries

        Returns:
            Formatted report string
        """
        duplicates = self.find_duplicates(metadata_list)

        if not duplicates:
            return "No duplicates found."

        lines = [f"Found {len(duplicates)} duplicate song groups:\n"]

        for i, (key, entries) in enumerate(sorted(duplicates.items()), 1):
            # Get title and artist from first entry
            title = entries[0].get("title", "Unknown")
            artist = entries[0].get("artist", "Unknown")
            album = entries[0].get("album", "Unknown")

            lines.append(f"{i}. '{title}' by {artist} (Album: {album})")
            lines.append(f"   {len(entries)} copies found:")

            for j, entry in enumerate(entries, 1):
                file_path = entry.get("file_path", "Unknown")
                lines.append(f"   [{j}] {file_path}")

            lines.append("")  # Empty line between groups

        return "\n".join(lines)
