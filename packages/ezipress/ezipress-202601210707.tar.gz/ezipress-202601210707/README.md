# ezipress - File Image Re-compression Tool

A file image re-compression tool that supports ZIP, RAR, and EPUB format image compression processing.

## Features

- **Multi-format Support**: Supports ZIP, RAR, and EPUB file formats
- **Smart Compression**: Automatically detects and compresses image files
- **Quality Control**: Configurable JPEG/WEBP quality parameters
- **Batch Processing**: Supports batch processing of large numbers of files
- **Compression Markers**: Adds compression markers to processed EPUB files to avoid reprocessing
- **Backup Mechanism**: Automatically creates backups and can restore on processing failure

## Installation

### System Requirements

- Python 3.8+
- Linux/macOS/Windows

### Installation Steps

```bash
# Install from PyPI
pip install ezipress

# Or install from source
git clone https://github.com/eyes1971/ezipress.git
cd ezipress
pip install -e .
```

### Optional Dependencies

```bash
# Install RAR support
pip install ezipress[rar]

# Install full functionality (includes all optional dependencies)
pip install ezipress[full]

# Install development dependencies
pip install ezipress[dev]
```

## Usage

### Basic Usage

```bash
# Compress a single file
ezipress file.zip

# Compress multiple files
ezipress file1.zip file2.epub file3.rar

# Process all supported files in a directory
ezipress /path/to/directory/

# Recursively process subdirectories
ezipress -r /path/to/directory/
```

### Advanced Options

```bash
# Set target file size (KB)
ezipress -t 1024000 file.zip

# Set JPEG quality (1-100)
ezipress -q 85 file.zip

# Set PNG to JPG threshold (KB)
ezipress -p 300 file.zip

# Enable debug mode
ezipress --debug file.zip
```

### Command Line Parameters

| Parameter | Description | Default |
|-----------|-------------|---------|
| `-t, --target-size` | Target file size (KB) | - |
| `-m, --min-size` | Skip images smaller than this size (KB) | 240 |
| `-q, --quality` | JPEG/WEBP quality reference value (1-100) | 95 |
| `-p, --png-to-jpg-threshold` | PNG to JPG threshold (KB) | 500 |
| `--webp-to-jpg-threshold` | WEBP to JPG threshold (KB) | 1024 |
| `-r, --recursive` | Recursively process subdirectories | No |
| `-f, --force` | Force recompression of marked EPUB files | No |
| `-s, --skip-compressed` | Automatically skip compressed EPUB files | No |
| `--add-marker` | Add compression markers to processed EPUB files | Yes |
| `--no-backup` | Do not keep backups of original files | No |
| `--workers` | Number of parallel worker processes | CPU cores |
| `--debug` | Enable debug mode | No |

## Project Structure

```
src/
├── cli.py              # Command line interface
├── main.py             # Main program logic
├── config.py           # Configuration management
├── typing.py           # Type definitions
├── archive/            # File format handlers
│   ├── epub_handler.py # EPUB handler
│   ├── zip_handler.py  # ZIP handler
│   ├── rar_handler.py  # RAR handler
│   └── marker.py       # Compression marker management
├── compressor/         # Image compression core
│   ├── core.py         # Compression core logic
│   ├── strategy.py     # Compression strategy
│   └── exceptions.py   # Custom exceptions
├── controller/         # Processing controllers
│   └── batch_controller.py    # Batch processing controller
├── display/            # Display interface
│   └── legacy_output.py # Traditional text output
└── utils/              # Utility functions
    ├── logger.py       # Logging management
    └── file_utils.py   # File utilities
```

## Development

### Setting up Development Environment

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest

# Format code
black src/
isort src/

# Check code
flake8 src/
mypy src/
```

### Building Release Version

```bash
# Build release version
python -m build

# Upload to PyPI
twine upload dist/*
```

## License

This project is licensed under the MIT License.

## Contributing

Issues and Pull Requests are welcome!

## Contact Information

- Author: Sam Weng
- Email: eyes1971@gmail.com
- Project Homepage: https://github.com/eyes1971/ezipress

