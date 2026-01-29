"""
日誌工具
"""

import logging
import sys
from typing import Optional
from pathlib import Path


def setup_logging(
    level: str = "INFO",
    log_file: Optional[str] = None,
    format_string: Optional[str] = None,
) -> None:
    """設置全域日誌系統"""
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # 根據日誌等級為控制台選擇不同格式
    if numeric_level > logging.DEBUG:
        console_format = "%(message)s"
    else:
        console_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # 如果使用者指定了 format_string，則覆蓋預設值
    if format_string is not None:
        console_format = format_string

    root_logger = logging.getLogger()
    # 確保 root logger 的等級是所有 handler 中最低的
    root_logger.setLevel(min(logging.DEBUG, numeric_level))

    # 清除既有的處理器
    for handler in root_logger.handlers[:]:
        root_logger.removeHandler(handler)

    # 控制台處理器
    console_formatter = logging.Formatter(console_format)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)

    # 檔案處理器（如果指定），總是使用詳細格式
    if log_file:
        try:
            log_path = Path(log_file)
            log_path.parent.mkdir(parents=True, exist_ok=True)

            file_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            file_formatter = logging.Formatter(file_format)

            file_handler = logging.FileHandler(log_file, encoding="utf-8")
            file_handler.setLevel(numeric_level)
            file_handler.setFormatter(file_formatter)
            root_logger.addHandler(file_handler)
        except Exception as e:
            # 此處是日誌系統本身初始化失敗，只能 print
            print(f"警告: 無法設置檔案日誌處理器: {e}", file=sys.stderr)


def get_logger(name: str, debug: bool = False) -> logging.Logger:
    """取得指定名稱的記錄器"""
    return logging.getLogger(name)


class LoggerMixin:
    """日誌混合類別 - 為其他類別提供日誌功能"""

    @property
    def logger(self) -> logging.Logger:
        """提供一個 logger 實例"""
        if not hasattr(self, "_logger"):
            self._logger = get_logger(
                self.__class__.__module__ + "." + self.__class__.__name__
            )
        return self._logger

    def log_debug(self, message: str) -> None:
        """記錄除錯訊息"""
        self.logger.debug(message)

    def log_info(self, message: str) -> None:
        """記錄資訊訊息"""
        self.logger.info(message)

    def log_warning(self, message: str) -> None:
        """記錄警告訊息，並強制另起一行避免黏在 UI"""
        sys.stdout.write("\r\n")  # 先換行，避免黏在 UI 最後一行
        sys.stdout.flush()
        self.logger.warning(message)

    def log_error(self, message: str) -> None:
        """記錄錯誤訊息"""
        self.logger.error(message)

    def log_exception(self, message: str) -> None:
        """記錄異常訊息（包含堆疊追蹤）"""
        self.logger.exception(message)

    def log_critical(self, message: str) -> None:
        """記錄嚴重錯誤訊息"""
        self.logger.critical(message)
