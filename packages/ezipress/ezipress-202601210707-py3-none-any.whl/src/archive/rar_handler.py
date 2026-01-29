"""
rar 處理
"""

import os
import tempfile
import shutil
import sys
import time
from pathlib import Path
from typing import Optional, Tuple, Any

from ..config import CompressorConfig
from ..compressor.core import ImageCompressor
from ..compressor.exceptions import InterruptedByUserError, DependencyError
from ..utils.logger import LoggerMixin
from .zip_handler import ZipHandler
from ..typing import GlobalControlProtocol


class RarHandler(LoggerMixin):
    """RAR 文件處理器"""

    def __init__(
        self, config: CompressorConfig, global_control: Optional[GlobalControlProtocol]
    ):
        self.config = config
        self.image_compressor = ImageCompressor(config, global_control)
        self.zip_handler = ZipHandler(config, global_control)

    def process_file(
        self,
        file_path: Path,
        global_control: GlobalControlProtocol,
        queue: Optional[Any],
    ) -> Tuple[bool, int, int, float, float, float, int]:
        """處理 RAR 檔案"""

        def send_update(msg_type: str, **payload):
            if queue:
                queue.put({"type": msg_type, "payload": payload})

        temp_dir = None
        processed_images = 0
        total_images = 0
        hit_rate_sum = 0.0
        original_size = self._get_file_size(file_path)
        compressed_size = original_size

        send_update("start_file", file_name=file_path.name)

        try:
            if not self._should_process_file(file_path, global_control, queue):
                send_update(
                    "finish_file",
                    success=True,
                    processed_images=0,
                    total_images=0,
                    size_before=original_size,
                    size_after=original_size,
                    hit_rate_sum=0.0,
                    hit_rate_count=0,
                )
                return True, 0, 0, original_size, original_size, 0.0, 0

            temp_dir = tempfile.mkdtemp()
            send_update("update_file_status", status="RAR 為只讀格式，將轉為 ZIP。")
            zip_path = file_path.with_suffix(".zip")

            # 檢查並導入 rarfile
            try:
                import rarfile
            except ImportError:
                raise DependencyError("處理 RAR 檔案需要 rarfile 庫。請執行: pip install rarfile")

            if not rarfile.is_rarfile(str(file_path)):
                raise ValueError(f"不是有效的 RAR 文件: {file_path}")

            if global_control and global_control.wait_if_paused():
                raise InterruptedByUserError

            send_update("update_file_status", status="解壓縮 RAR...")

            with rarfile.RarFile(str(file_path), "r") as rar_ref:
                # 掃描圖片檔案
                image_list = [
                    f.filename
                    for f in rar_ref.infolist()
                    if Path(f.filename).suffix.lower()
                    in self.image_compressor.SUPPORTED_FORMATS
                ]
                total_images = len(image_list)
                send_update("update_file_progress", completed=0, total=total_images)
                rar_ref.extractall(temp_dir)

            if global_control and global_control.wait_if_paused():
                raise InterruptedByUserError

            send_update("update_file_status", status="RAR 解壓完成，開始處理圖片...")

            archive_config = self.config.get_archive_config(".zip")
            compression_params = self.config.get_compression_params()

            result = self.image_compressor.process_directory(
                temp_dir,
                compression_params,
                archive_config,
                global_control,
                queue,
                total_images,
            )
            files_to_repack, processed_images, modified, _, _, _, hit_rate_sum = result

            if global_control and global_control.should_exit:
                raise InterruptedByUserError

            if modified:
                send_update("update_file_status", status="重新打包為 ZIP 文件...")
                self._repack_to_zip(zip_path, files_to_repack, temp_dir, global_control)
                compressed_size = self._get_file_size(zip_path)
                send_update(
                    "update_file_status",
                    status=f"轉換完成: {file_path.name} -> {zip_path.name}",
                )
            else:
                send_update("update_file_status", status=f"無需處理: {file_path.name}")

            send_update(
                "finish_file",
                success=True,
                processed_images=processed_images,
                total_images=total_images,
                size_before=original_size,
                size_after=compressed_size,
                hit_rate_sum=hit_rate_sum,
                hit_rate_count=processed_images,
            )
            return (
                True,
                processed_images,
                total_images,
                original_size,
                compressed_size,
                hit_rate_sum,
                processed_images,
            )

        except InterruptedByUserError:
            self.log_warning(f"處理檔案 {file_path.name} 的操作被使用者中斷。")
            send_update(
                "finish_file",
                success=False,
                processed_images=processed_images,
                total_images=total_images,
                size_before=original_size,
                size_after=original_size,
                hit_rate_sum=0.0,
                hit_rate_count=0,
            )
            return (
                False,
                processed_images,
                total_images,
                original_size,
                original_size,
                0.0,
                0,
            )
        except Exception:
            self.log_exception(f"處理 RAR {file_path.name} 時發生未預期的錯誤")
            send_update(
                "finish_file",
                success=False,
                processed_images=0,
                total_images=total_images,
                size_before=original_size,
                size_after=original_size,
                hit_rate_sum=0.0,
                hit_rate_count=0,
            )
            return False, 0, total_images, original_size, original_size, 0.0, 0
        finally:
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)

    def _get_file_size(self, file_path: Path) -> float:
        """取得檔案大小（KB）"""
        try:
            return file_path.stat().st_size / 1024 if file_path.exists() else 0.0
        except (OSError, AttributeError):
            return 0.0

    def _should_process_file(
        self,
        file_path: Path,
        global_control: GlobalControlProtocol,
        queue: Optional[Any],
    ) -> bool:
        """檢查是否應該處理 RAR 檔案"""

        def send_update(msg_type: str, **payload):
            if queue:
                queue.put({"type": msg_type, "payload": payload})

        try:
            import rarfile

            if not rarfile.is_rarfile(str(file_path)):
                send_update(
                    "update_file_status", status=f"無效的 RAR 文件: {file_path.name}"
                )
                return False
        except ImportError:
            self.log_error("未安裝 rarfile 庫，無法處理 RAR 檔案。請執行 'pip install rarfile'")
            send_update("update_file_status", status="未安裝 rarfile 庫")
            return False

        # 在批次模式下自動跳過詢問
        if (
            not queue
            or not global_control
            or not hasattr(global_control, "get_user_response_sync")
        ):
            self.log_info(f"非互動模式下，自動跳過 RAR 轉 ZIP 的詢問: {file_path.name}")
            return False

        # 自動轉換（在互動模式下）
        send_update("update_file_status", status="RAR 將自動轉換為 ZIP")
        time.sleep(1)
        return True

    def _repack_to_zip(
        self,
        zip_path: Path,
        files_to_repack: list,
        temp_dir: str,
        global_control: GlobalControlProtocol,
    ):
        """重新打包為 ZIP 格式"""
        import zipfile

        try:
            with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zip_ref:
                for idx, f_info in enumerate(files_to_repack):
                    if global_control:
                        global_control.wait_if_paused()
                    if global_control and idx % 20 == 0 and global_control.should_exit:
                        raise InterruptedByUserError

                    source_path = Path(f_info["src"])
                    archive_name = f_info["arc"]
                    if source_path.exists():
                        zip_ref.write(str(source_path), archive_name)
                    else:
                        self.log_warning(f"文件 {source_path.name} 不存在，跳過")
        except Exception as e:
            self.log_error(f"重新打包為 ZIP 時發生錯誤: {e}")
            raise
