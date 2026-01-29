"""
epub 標記邏輯
"""

import json
import zipfile
from datetime import datetime
from typing import Dict, Any

from ..utils.logger import LoggerMixin
from .. import __version__


class CompressionMarker(LoggerMixin):
    """壓縮標記管理器"""

    MARKER_PATH = "META-INF/compression_marker.json"

    def check_compression_marker(self, file_path: str) -> Dict[str, Any]:
        """檢查檔案是否已被壓縮過"""
        try:
            with zipfile.ZipFile(file_path, "r") as zf:
                if self.MARKER_PATH in zf.namelist():
                    with zf.open(self.MARKER_PATH) as marker_file:
                        marker_data = json.load(marker_file)
                        return {"is_compressed": True, "data": marker_data}
        except (
            zipfile.BadZipFile,
            FileNotFoundError,
            json.JSONDecodeError,
            KeyError,
        ) as e:
            self.log_debug(f"檢查壓縮標記時發生預期內的錯誤: {e}")
        except Exception as e:
            self.log_warning(f"檢查壓縮標記時發生未預期的錯誤: {e}")

        return {"is_compressed": False}

    def add_compression_marker(
        self, zip_ref: zipfile.ZipFile, settings: Dict[str, Any]
    ) -> None:
        """添加壓縮標記到 ZIP 檔案"""
        marker_data = {
            "tool": "src",
            "version": __version__,
            "compressed_date": datetime.now().isoformat(),
            "settings": settings,
        }

        try:
            zip_ref.writestr(
                self.MARKER_PATH, json.dumps(marker_data, indent=2, ensure_ascii=False)
            )
            self.log_debug("已添加壓縮標記")
        except Exception as e:
            self.log_warning(f"添加壓縮標記失敗: {e}")

    def get_marker_info(self, marker_data: Dict[str, Any]) -> str:
        """取得標記資訊摘要"""
        if not marker_data or not isinstance(marker_data, dict):
            return "無效標記"

        version = marker_data.get("version", "未知")
        date_str = marker_data.get("compressed_date", "未知")
        tool = marker_data.get("tool", "未知工具")

        # 簡化日期顯示
        try:
            if date_str != "未知":
                date_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
                date_str = date_obj.strftime("%Y-%m-%d %H:%M")
        except (ValueError, AttributeError):
            pass

        return f"工具: {tool}, 版本: {version}, 日期: {date_str}"
