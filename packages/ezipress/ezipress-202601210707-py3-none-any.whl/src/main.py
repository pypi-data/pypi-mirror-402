"""
Main process orchestrator - coordinates execution of various modules
"""

import signal
from pathlib import Path

from .config import CompressorConfig
from .controller import batch_controller
from .utils.logger import get_logger
from .compressor.exceptions import FatalError, InterruptedByUserError


class CompressorMain:
    """Main process orchestrator"""

    def __init__(self, config: CompressorConfig):
        self.config = config
        self.logger = get_logger(__name__, debug=config.debug)
        self.controller = None
        self._setup_handlers()

    def _setup_handlers(self):
        """Initialize handlers"""
        # Use traditional output mode
        self.controller = batch_controller.BatchController(self.config)

    def _signal_handler(self, signum, frame):
        """Gracefully handle Ctrl+C"""
        self.logger.info("Received SIGINT (Ctrl+C), preparing to exit...")
        if self.controller and hasattr(self.controller, "exit"):
            self.controller.exit()

    def run(self) -> int:
        """Execute main process"""
        signal.signal(signal.SIGINT, self._signal_handler)
        exit_code = 0

        try:
            exit_code = self.controller.run_processing()
        except FatalError as e:
            self.logger.critical(
                f"Fatal error occurred, program terminating: {e}")
            exit_code = 1
        except InterruptedByUserError:
            self.logger.warning(
                "User interrupted operation. Program terminated.")
            exit_code = 130
        except Exception as e:
            self.logger.exception(
                f"Unexpected error during main process execution: {e}")
            exit_code = 1
        finally:
            if self.controller and hasattr(self.controller, "cleanup"):
                self.controller.cleanup()

        return exit_code

    def get_handler_for_file(self, file_path: Path):
        """Get corresponding handler based on file type"""
        from .archive.epub_handler import EpubHandler
        from .archive.zip_handler import ZipHandler
        from .archive.rar_handler import RarHandler

        extension = file_path.suffix.lower()
        global_control = getattr(self.controller, "global_control", None)

        handler_map = {".epub": EpubHandler,
                       ".zip": ZipHandler, ".rar": RarHandler}

        if extension not in handler_map:
            raise ValueError(f"Unsupported file format: {extension}")

        return handler_map[extension](self.config, global_control)
