"""
Configuration management - unified management of all configuration parameters
"""

import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import List, Optional


@dataclass
class CompressorConfig:
    """Compressor configuration class"""

    # File related
    files_to_process: List[Path] = field(default_factory=list)
    recursive: bool = False

    # Compression parameters
    target_size: Optional[int] = None
    min_size: int = 240
    quality: int = 95
    png_to_jpg_threshold: int = 500
    webp_to_jpg_threshold: int = 1024

    # Behavior control
    force: bool = False
    skip_compressed: bool = False
    add_marker: bool = False
    keep_backup: bool = True

    # Execution mode
    workers: int = 1
    debug: bool = False

    # Display settings
    enable_colors: bool = True
    verbose: bool = False

    def __post_init__(self):
        """Post-initialization processing"""
        # Adjust color support based on platform
        if sys.platform == "win32":
            try:
                import colorama

                colorama.init()
            except ImportError:
                self.enable_colors = False

        # Ensure parameters are within reasonable ranges
        self.workers = max(1, self.workers)
        self.quality = max(1, min(100, self.quality))
        self.min_size = max(0, self.min_size)

    @classmethod
    def from_args(cls, args) -> "CompressorConfig":
        """Create configuration object from command line arguments"""
        return cls(
            target_size=args.target_size,
            min_size=args.min_size,
            quality=args.quality,
            png_to_jpg_threshold=args.png_to_jpg_threshold,
            webp_to_jpg_threshold=args.webp_to_jpg_threshold,
            recursive=args.recursive,
            force=args.force,
            skip_compressed=args.skip_compressed,
            add_marker=args.add_marker,
            keep_backup=args.keep_backup,
            workers=args.workers,
            debug=args.debug,
        )

    def get_archive_config(self, file_extension: str) -> dict:
        """Get file format specific settings"""
        is_epub = file_extension == ".epub"
        return {
            "png_to_jpg_threshold": self.png_to_jpg_threshold,
            "webp_to_jpg_threshold": self.webp_to_jpg_threshold,
            "is_epub": is_epub,
            "add_marker": self.add_marker or is_epub,
        }

    def get_compression_params(self) -> dict:
        """Get compression parameters"""
        return {
            "target_size": self.target_size,
            "min_size": self.min_size,
            "quality": self.quality,
        }

    def validate(self) -> List[str]:
        """Validate settings and return warning messages"""
        warnings = []

        if not self.target_size:
            warnings.append(
                "No target size specified, image compression will not be performed")

        if self.quality < 1 or self.quality > 100:
            warnings.append(
                f"Quality parameter {self.quality} out of range (1-100)")

        if self.min_size < 0:
            warnings.append("Minimum file size cannot be negative")

        if self.workers < 1:
            warnings.append("Number of worker processes cannot be less than 1")

        return warnings
