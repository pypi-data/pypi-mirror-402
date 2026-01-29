"""
Custom types and protocols for static analysis.
"""

from typing import Protocol, Optional


class GlobalControlProtocol(Protocol):
    """
    Protocol for the global control object that manages application state like pause/exit.
    """

    should_exit: bool
    is_paused: bool

    def wait_if_paused(self) -> bool:
        """Blocks if the process is paused, returns True if it should exit."""
        ...

    def get_user_response_sync(self, prompt_message: str, timeout: float = 30.0) -> str:
        """Synchronously prompts the user and waits for a response."""
        ...

    def pause(self) -> None:
        ...

    def resume(self) -> None:
        ...

    def exit(self) -> None:
        ...

    def set_user_response(self, response: str) -> None:
        ...


class ProgressDisplayProtocol(Protocol):
    """
    Protocol for any class that displays progress of the compression.
    """

    def start(self) -> None:
        ...

    def stop(self) -> None:
        ...

    def show_summary(self) -> None:
        ...

    def set_prompt(self, message: Optional[str]) -> None:
        ...

    def start_file(self, file_index: int, filename: str, **kwargs) -> None:
        ...

    def finish_file(
        self,
        success: bool,
        processed_images: int,
        total_images: int,
        original_size: float,
        compressed_size: float,
        hit_rate_sum: float,
        successful_images: int,
    ) -> None:
        ...

    def start_image(
        self, image_name: str, original_size_kb: float, target_size_kb: float
    ) -> None:
        ...

    def finish_image(
        self, success: bool, final_size_kb: Optional[float] = None
    ) -> None:
        ...

    def update_file_status(self, status: str) -> None:
        ...

    def update_iteration(
        self, current: int, total: int, hit_rate: Optional[float] = None
    ) -> None:
        ...

    def update_compression_params(
        self, quality: float, scale: float, current_size: float
    ) -> None:
        ...

    def update_file_progress(self, completed: int, total: int) -> None:
        ...
