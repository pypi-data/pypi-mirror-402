# ===================
# src/__init__.py
# ===================
#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
壓縮檔案圖片重新壓縮工具

支援 ZIP、RAR、EPUB 格式的圖片壓縮處理，提供互動式進度顯示和批次處理模式。
"""

from .main import CompressorMain
from .config import CompressorConfig
import datetime

__version__ = datetime.datetime.now().strftime("%Y%m%d%H%M")
__author__ = "Sam Weng"
__email__ = "eyes1971@gmail.com"
__license__ = "MIT"


def get_version():
    """動態生成版本號，使用當前時間戳"""
    return datetime.datetime.now().strftime("%Y%m%d%H%M")


# 主要模組導入

# 便捷函數


def create_compressor(config_dict: dict | None = None):
    """建立壓縮器實例的便捷函數"""
    if config_dict is None:
        config_dict = {}
    config = CompressorConfig(**config_dict)
    return CompressorMain(config)


__all__ = ["CompressorConfig", "CompressorMain",
           "create_compressor", "__version__"]
