"""
no-progress 模式輸出（可選）
"""

import sys
from typing import Optional


class LegacyOutput:
    """傳統輸出模式，適用於非互動式環境"""

    def __init__(self, enable_colors: bool = True):
        self.enable_colors = enable_colors and sys.stdout.isatty()

    def print_info(self, message: str):
        """輸出資訊訊息"""
        print(f"ℹ️  {message}")

    def print_success(self, message: str):
        """輸出成功訊息"""
        if self.enable_colors:
            print(f"\033[92m✅ {message}\033[0m")
        else:
            print(f"✅ {message}")

    def print_error(self, message: str):
        """輸出錯誤訊息"""
        if self.enable_colors:
            print(f"\033[91m❌ {message}\033[0m", file=sys.stderr)
        else:
            print(f"❌ {message}", file=sys.stderr)

    def print_warning(self, message: str):
        """輸出警告訊息"""
        if self.enable_colors:
            print(f"\033[93m⚠️  {message}\033[0m")
        else:
            print(f"⚠️  {message}")

    def print_progress(self, current: int, total: int, message: str = ""):
        """輸出進度"""
        if total <= 0:
            return

        percentage = (current / total) * 100
        bar_length = 30
        filled_length = int(bar_length * current // total)
        bar = "█" * filled_length + "░" * (bar_length - filled_length)

        if self.enable_colors:
            print(
                f"\r\033[96m[{bar}] {current}/{total} ({percentage:.1f}%)\033[0m {message}",
                end="",
                flush=True,
            )
        else:
            print(
                f"\r[{bar}] {current}/{total} ({percentage:.1f}%) {message}",
                end="",
                flush=True,
            )

    def print_file_result(
        self,
        success: bool,
        filename: str,
        processed_images: int,
        total_images: int,
        size_before: float,
        size_after: float,
    ):
        """輸出檔案處理結果"""
        status = "完成" if success else "失敗"
        status_icon = "✅" if success else "❌"

        message = f"{status_icon} {status}: {filename} (圖片: {processed_images}/{total_images}, {size_before:.1f}KB -> {size_after:.1f}KB)"

        if success:
            self.print_success(message)
        else:
            self.print_error(message)
