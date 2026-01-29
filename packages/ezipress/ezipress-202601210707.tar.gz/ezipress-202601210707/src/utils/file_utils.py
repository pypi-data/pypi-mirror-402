"""
檔案工具
"""

import os
from pathlib import Path
from typing import List, Optional, Set

from .logger import LoggerMixin


class FileScanner(LoggerMixin):
    """檔案掃描器"""

    def scan_directory(
        self,
        directory: str,
        extensions: Optional[Set[str]] = None,
        recursive: bool = True,
    ) -> List[Path]:
        """掃描目錄中的檔案"""
        directory_path = Path(directory)

        if not directory_path.exists():
            self.log_error(f"目錄不存在: {directory}")
            return []

        if not directory_path.is_dir():
            self.log_error(f"不是有效目錄: {directory}")
            return []

        files = []

        try:
            pattern = "**/*" if recursive else "*"

            for file_path in directory_path.glob(pattern):
                if not file_path.is_file():
                    continue

                if extensions is None or file_path.suffix.lower() in extensions:
                    files.append(file_path)

        except (OSError, PermissionError) as e:
            self.log_exception(f"掃描目錄 {directory} 時發生錯誤: {e}")

        return sorted(files)

    def get_file_info(self, file_path: str) -> dict:
        """取得檔案資訊"""
        path = Path(file_path)

        try:
            if not path.exists():
                return {
                    "path": str(path),
                    "name": path.name,
                    "suffix": path.suffix.lower(),
                    "size": 0,
                    "size_kb": 0.0,
                    "size_mb": 0.0,
                    "modified": 0,
                    "exists": False,
                }

            stat = path.stat()
            return {
                "path": str(path),
                "name": path.name,
                "suffix": path.suffix.lower(),
                "size": stat.st_size,
                "size_kb": stat.st_size / 1024,
                "size_mb": stat.st_size / (1024 * 1024),
                "modified": stat.st_mtime,
                "exists": True,
            }
        except (OSError, PermissionError) as e:
            self.log_warning(f"無法取得檔案資訊 {file_path}: {e}")
            return {
                "path": str(path),
                "name": path.name,
                "suffix": path.suffix.lower() if path.suffix else "",
                "size": 0,
                "size_kb": 0.0,
                "size_mb": 0.0,
                "modified": 0,
                "exists": False,
                "error": str(e),
            }

    def validate_archive_file(self, file_path: str, file_type: str = "auto") -> bool:
        """驗證壓縮檔案有效性"""
        path = Path(file_path)

        if not path.exists() or not path.is_file():
            return False

        # 自動檢測檔案類型
        if file_type == "auto":
            extension = path.suffix.lower()
            if extension in [".zip", ".epub"]:
                file_type = "zip"
            elif extension == ".rar":
                file_type = "rar"
            else:
                return False

        try:
            if file_type == "zip":
                import zipfile

                return zipfile.is_zipfile(str(path))
            elif file_type == "rar":
                try:
                    import rarfile

                    return rarfile.is_rarfile(str(path))
                except ImportError:
                    self.log_warning("未安裝 rarfile，無法驗證 RAR 檔案")
                    return False
            else:
                return False

        except Exception as e:
            self.log_debug(f"驗證檔案 {file_path} 時發生錯誤: {e}")
            return False
