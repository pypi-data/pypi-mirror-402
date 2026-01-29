#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CLI entry point - handles command line parameter parsing and program startup
"""

import argparse
import os
from pathlib import Path

from .config import CompressorConfig
from .main import CompressorMain
from . import __version__
from .utils.logger import setup_logging, get_logger


def create_argument_parser():
    """Create command line argument parser"""
    parser = argparse.ArgumentParser(
        description=f"File image re-compression tool v{__version__}",
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument("files", nargs="+",
                        help="File paths to process (ZIP, RAR, EPUB) or directories containing them")

    parser.add_argument("-t", "--target-size", type=int,
                        help="Target file size (KB)")

    parser.add_argument(
        "-m", "--min-size", type=int, default=240, help="Skip images smaller than this size (KB, default: 240)"
    )

    parser.add_argument(
        "-q", "--quality", type=int, default=95, help="JPEG/WEBP quality reference value (1-100, default: 95)"
    )

    parser.add_argument(
        "-p",
        "--png-to-jpg-threshold",
        type=int,
        default=500,
        help="Convert PNG to JPG in ZIP/RAR if larger than this size (KB, default: 500)",
    )

    parser.add_argument(
        "--webp-to-jpg-threshold",
        type=int,
        default=1024,
        help="Convert WEBP to JPG in ZIP/RAR if larger than this size (KB, default: 1024)",
    )

    parser.add_argument("-r", "--recursive",
                        action="store_true", help="Recursively process subdirectories")

    parser.add_argument(
        "-f", "--force", action="store_true", help="Force recompression of marked EPUB files")

    parser.add_argument(
        "-s", "--skip-compressed", action="store_true", help="Automatically skip compressed EPUB files"
    )

    parser.add_argument(
        "--add-marker", action="store_true", help="Add compression markers to processed EPUB files (enabled by default for EPUB)"
    )

    parser.add_argument(
        "--no-backup",
        dest="keep_backup",
        action="store_false",
        help="Do not keep backups of original files (kept by default)",
    )

    parser.add_argument(
        "--workers",
        type=int,
        default=os.cpu_count(),
        help=f"Number of parallel worker processes (default: {os.cpu_count()})",
    )

    parser.add_argument("--version", action="version",
                        version=f"Compression tool v{__version__}")

    parser.add_argument("--debug", action="store_true",
                        help="Enable debug mode")

    return parser


def validate_arguments(args):
    """Validate command line arguments"""
    logger = get_logger(__name__)

    # Validate worker count
    max_workers = os.cpu_count() or 1
    if args.workers > max_workers:
        args.workers = max_workers
        logger.warning(
            f"Specified worker count exceeds system CPU cores, adjusted to {args.workers}")
    elif args.workers < 1:
        args.workers = 1
        logger.warning("Worker count cannot be less than 1, adjusted to 1")

    # Check if target size is specified
    if not args.target_size:
        logger.warning(
            "No -t/--target-size specified. Image compression will not be performed.")

    # Validate quality parameter
    if args.quality < 1 or args.quality > 100:
        args.quality = max(1, min(100, args.quality))
        logger.warning(
            f"Quality parameter adjusted to valid range: {args.quality}")

    return args


def collect_input_files(args):
    """Collect files to process"""
    files_to_process = []
    supported_extensions = {".zip", ".rar", ".epub"}

    for path_str in args.files:
        path = Path(path_str)

        if not path.exists():
            get_logger(__name__).warning(
                f"Path does not exist, skipping: {path_str}")
            continue

        if path.is_file() and path.suffix.lower() in supported_extensions:
            files_to_process.append(path)
        elif path.is_dir():
            try:
                glob_pattern = "**/*" if args.recursive else "*"
                found_files = [
                    p
                    for p in path.glob(glob_pattern)
                    if p.is_file() and p.suffix.lower() in supported_extensions
                ]
                files_to_process.extend(found_files)
            except (OSError, PermissionError) as e:
                get_logger(__name__).warning(
                    f"Cannot access directory {path_str}: {e}")

    return sorted(list(set(files_to_process)))


def main():
    """CLI main entry point"""
    # Set up basic logger first
    setup_logging()
    logger = get_logger(__name__)

    try:
        # Parse command line arguments
        parser = create_argument_parser()
        parser.set_defaults(keep_backup=True)
        args = parser.parse_args()

        # Reset logger level if debug mode is enabled
        if args.debug:
            # Create debug log file in current directory
            import datetime
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = f"ezipress_debug_{timestamp}.log"
            setup_logging(level="DEBUG", log_file=log_file)
            logger.info(
                f"Debug mode enabled. Logs will be saved to: {log_file}")

        # Validate arguments
        args = validate_arguments(args)

        # Collect files
        files_to_process = collect_input_files(args)

        if not files_to_process:
            logger.warning("No supported files found.")
            return 1

        # Create configuration object
        config = CompressorConfig.from_args(args)
        config.files_to_process = files_to_process

        # Execute main program
        main_processor = CompressorMain(config)
        return main_processor.run()

    except KeyboardInterrupt:
        logger.warning("\nOperation cancelled by user.")
        return 130
    except Exception as e:
        logger.exception(
            f"Unexpected critical error during CLI execution: {e}")
        return 1
