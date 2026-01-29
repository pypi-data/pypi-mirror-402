"""Command-line interface for MusicList for Soundiiz."""

import argparse
import logging
import sys
from pathlib import Path
from typing import Optional

from . import __version__
from .duplicate_detector import DuplicateDetector
from .exporter import get_exporter
from .extractor import MusicFileExtractor

logger = logging.getLogger(__name__)


def setup_logging(verbose: bool = False) -> None:
    """
    Configure logging.

    Args:
        verbose: Enable verbose (DEBUG) logging
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def parse_args(args: Optional[list] = None) -> argparse.Namespace:
    """
    Parse command-line arguments.

    Args:
        args: Arguments to parse (defaults to sys.argv)

    Returns:
        Parsed arguments
    """
    parser = argparse.ArgumentParser(
        description="Extract music file metadata for Soundiiz import",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Extract metadata from directory to CSV (default)
  musiclist-for-soundiiz -i /path/to/music -o output.csv

  # Export to JSON format
  musiclist-for-soundiiz -i /path/to/music -o output.json -f json

  # Only scan MP3 and FLAC files
  musiclist-for-soundiiz -i /path/to/music -e .mp3 .flac

  # Non-recursive scan (current directory only)
  musiclist-for-soundiiz -i /path/to/music --no-recursive

  # Batch processing multiple directories
  musiclist-for-soundiiz -i /path/to/music1 /path/to/music2 -o output.csv

  # Detect and remove duplicates
  musiclist-for-soundiiz -i /path/to/music --remove-duplicates -o output.csv

  # Save duplicate detection report
  musiclist-for-soundiiz -i /path/to/music --detect-duplicates --duplicate-report duplicates.txt

Supported audio formats:
  AAC (.aac), AU (.au), FLAC (.flac), MP3 (.mp3), OGG (.ogg),
  M4A (.m4a), WAV (.wav), WMA (.wma)
        """,
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}",
    )

    # Input/Output arguments
    io_group = parser.add_argument_group("Input/Output")
    io_group.add_argument(
        "-i",
        "--input",
        nargs="+",
        required=True,
        help="Path(s) to music directory/directories to scan (supports multiple directories for batch processing)",
    )
    io_group.add_argument(
        "-o",
        "--output",
        default="output.csv",
        help="Output file path (default: output.csv)",
    )
    io_group.add_argument(
        "-f",
        "--format",
        choices=["csv", "json", "m3u", "txt"],
        default="csv",
        help="Output format (default: csv)",
    )

    # Scan options
    scan_group = parser.add_argument_group("Scan Options")
    scan_group.add_argument(
        "-e",
        "--extensions",
        nargs="+",
        help="File extensions to include (e.g., .mp3 .flac). Default: all supported formats",
    )
    scan_group.add_argument(
        "--no-recursive",
        action="store_true",
        help="Don't scan subdirectories recursively",
    )

    # Export options
    export_group = parser.add_argument_group("Export Options")
    export_group.add_argument(
        "--max-songs-per-file",
        type=int,
        default=200,
        help="Maximum songs per file when splitting (default: 200)",
    )
    export_group.add_argument(
        "--no-pretty-json",
        action="store_true",
        help="Disable pretty-printing for JSON output",
    )

    # Duplicate detection options
    dup_group = parser.add_argument_group("Duplicate Detection")
    dup_group.add_argument(
        "--detect-duplicates",
        action="store_true",
        help="Detect and report duplicate songs",
    )
    dup_group.add_argument(
        "--remove-duplicates",
        action="store_true",
        help="Remove duplicate songs from export",
    )
    dup_group.add_argument(
        "--duplicate-strategy",
        choices=["keep_first", "keep_last", "keep_shortest_path"],
        default="keep_first",
        help="Strategy for keeping duplicates (default: keep_first)",
    )
    dup_group.add_argument(
        "--duplicate-report",
        type=str,
        metavar="FILE",
        help="Save duplicate detection report to file",
    )

    # Logging options
    log_group = parser.add_argument_group("Logging")
    log_group.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="Enable verbose (DEBUG) logging",
    )
    log_group.add_argument(
        "-q",
        "--quiet",
        action="store_true",
        help="Suppress all output except errors",
    )

    parsed_args = parser.parse_args(args)

    # Validate arguments
    if parsed_args.quiet and parsed_args.verbose:
        parser.error("Cannot use --quiet and --verbose together")

    return parsed_args


def main(argv: Optional[list] = None) -> int:
    """
    Main entry point for the CLI.

    Args:
        argv: Command-line arguments (defaults to sys.argv)

    Returns:
        Exit code (0 for success, non-zero for failure)
    """
    args = parse_args(argv)

    # Setup logging
    if args.quiet:
        logging.basicConfig(level=logging.ERROR)
    else:
        setup_logging(args.verbose)

    logger.info(f"MusicList for Soundiiz v{__version__}")
    
    # Support batch processing of multiple directories
    input_dirs = args.input if isinstance(args.input, list) else [args.input]
    logger.info(f"Scanning {len(input_dirs)} director{'ies' if len(input_dirs) > 1 else 'y'}...")

    try:
        # Validate input directories
        for input_dir in input_dirs:
            input_path = Path(input_dir)
            if not input_path.exists():
                logger.error(f"Input directory does not exist: {input_dir}")
                return 1
            if not input_path.is_dir():
                logger.error(f"Input path is not a directory: {input_dir}")
                return 1

        # Initialize extractor
        extractor = MusicFileExtractor(include_extensions=args.extensions)

        # Extract metadata from all directories
        all_metadata = []
        for input_dir in input_dirs:
            logger.info(f"Extracting metadata from: {input_dir}")
            metadata_list = extractor.extract_all(
                directory=str(input_dir),
                recursive=not args.no_recursive,
            )
            all_metadata.extend(metadata_list)
            logger.info(f"  Found {len(metadata_list)} files in {input_dir}")

        if not all_metadata:
            logger.warning("No music files found!")
            return 0

        logger.info(f"Successfully extracted metadata from {len(all_metadata)} total files")

        # Duplicate detection and removal
        metadata_to_export = all_metadata
        if args.detect_duplicates or args.remove_duplicates or args.duplicate_report:
            detector = DuplicateDetector(case_sensitive=False)
            
            if args.detect_duplicates or args.duplicate_report:
                logger.info("Detecting duplicates...")
                duplicates = detector.find_duplicates(all_metadata)
                
                if duplicates:
                    logger.warning(
                        f"Found {len(duplicates)} duplicate song groups "
                        f"({sum(len(v) for v in duplicates.values())} total files)"
                    )
                    
                    # Generate and save/display report
                    report = detector.get_duplicate_report(all_metadata)
                    
                    if args.duplicate_report:
                        with open(args.duplicate_report, "w", encoding="utf-8") as f:
                            f.write(report)
                        logger.info(f"Duplicate report saved to: {args.duplicate_report}")
                    else:
                        print("\n" + report)
                else:
                    logger.info("No duplicates found.")
            
            if args.remove_duplicates:
                logger.info(f"Removing duplicates (strategy: {args.duplicate_strategy})...")
                unique_list, removed_list = detector.remove_duplicates(
                    all_metadata, strategy=args.duplicate_strategy
                )
                metadata_to_export = unique_list
                logger.info(
                    f"Removed {len(removed_list)} duplicates, "
                    f"{len(unique_list)} unique songs remaining"
                )
        
        # Use the (possibly filtered) metadata for export
        if not metadata_to_export:
            logger.warning("No songs to export after duplicate removal!")
            return 0

        # Initialize exporter
        exporter_kwargs = {}
        if args.format == "csv":
            exporter_kwargs["max_songs_per_file"] = args.max_songs_per_file
        elif args.format == "json":
            exporter_kwargs["pretty"] = not args.no_pretty_json
            exporter_kwargs["max_songs_per_file"] = args.max_songs_per_file
        elif args.format == "m3u":
            exporter_kwargs["max_songs_per_file"] = args.max_songs_per_file
        elif args.format == "txt":
            exporter_kwargs["max_songs_per_file"] = args.max_songs_per_file

        exporter = get_exporter(args.format, **exporter_kwargs)

        # Export metadata
        logger.info(f"Exporting {len(metadata_to_export)} songs to {args.format.upper()} format: {args.output}")
        exporter.export(metadata_to_export, args.output)

        logger.info("✓ Export completed successfully!")
        return 0

    except KeyboardInterrupt:
        logger.error("\nOperation cancelled by user")
        return 130

    except Exception as e:
        logger.error(f"Error: {e}", exc_info=args.verbose)
        return 1


if __name__ == "__main__":
    sys.exit(main())
