"""
epub 專用（含標記、mimetype等）
"""

import os
import zipfile
import tempfile
import shutil
import time
from pathlib import Path
from typing import Optional, Tuple, Any

from ..config import CompressorConfig
from ..compressor.core import ImageCompressor
from ..compressor.exceptions import InterruptedByUserError, FatalError
from ..utils.logger import LoggerMixin
from .marker import CompressionMarker
from ..typing import GlobalControlProtocol


class EpubHandler(LoggerMixin):
    def _repack_archive(
        self,
        file_path: Path,
        files_to_repack: list,
        temp_dir: str,
        archive_config: dict,
        global_control: GlobalControlProtocol,
        queue: Optional[Any],
        modified: bool = False,
    ):
        """重新打包 EPUB 檔案（含 mimetype 與壓縮標記）"""
        backup_path = file_path.with_suffix(file_path.suffix + ".backup")

        if global_control and global_control.should_exit:
            raise InterruptedByUserError

        # 建立備份
        try:
            shutil.copy2(file_path, backup_path)
        except Exception as e:
            self.log_exception("建立備份失敗，中止操作")
            raise FatalError(f"無法為 {file_path.name} 建立備份: {e}") from e

        try:
            send_update = (
                lambda msg, **payload: queue.put(
                    {"type": msg, "payload": payload})
                if queue
                else None
            )
            send_update("update_file_status", status="重新打包 EPUB...")

            with zipfile.ZipFile(file_path, "w", zipfile.ZIP_DEFLATED) as zip_ref:
                # 先處理 mimetype 檔案（必須不壓縮且為第一個檔案）
                mimetype_path = Path(temp_dir) / "mimetype"
                if mimetype_path.is_file():
                    zip_ref.write(
                        str(mimetype_path), "mimetype", compress_type=zipfile.ZIP_STORED
                    )

                # 處理其他檔案
                for idx, f_info in enumerate(files_to_repack):
                    if global_control:
                        global_control.wait_if_paused()
                    if global_control and idx % 20 == 0 and global_control.should_exit:
                        raise InterruptedByUserError

                    source_path = Path(f_info["src"])
                    archive_name = f_info["arc"]

                    # 跳過 mimetype（已經處理過）
                    if archive_name == "mimetype":
                        continue

                    if source_path.exists():
                        zip_ref.write(str(source_path), archive_name)
                    else:
                        self.log_warning(f"檔案 {source_path.name} 不存在，跳過")

                # 添加壓縮標記（如果有修改且設定要添加）
                if modified and archive_config.get("add_marker", False):
                    if global_control and global_control.should_exit:
                        raise InterruptedByUserError
                    settings = {
                        k: v
                        for k, v in archive_config.items()
                        if k not in ["add_marker", "is_epub"]
                    }
                    self.marker.add_compression_marker(zip_ref, settings)

            # 清理備份檔案
            if not self.config.keep_backup and backup_path.exists():
                try:
                    backup_path.unlink()
                except OSError as e:
                    self.log_warning(f"無法刪除備份檔案: {e}")

        except Exception as e:
            self.log_exception(f"重新打包失敗或被中斷: {e}。正在從備份還原...")
            send_update("update_file_status", status="錯誤/中斷，還原檔案中...")

            # 從備份還原
            try:
                if backup_path.exists():
                    shutil.move(str(backup_path), str(file_path))
                    self.log_info(f"成功從 {backup_path.name} 還原檔案。")
            except Exception as restore_err:
                self.log_critical(f"從備份還原檔案時發生嚴重錯誤: {restore_err}")
            raise

    def _should_process_file(
        self, file_path: Path, global_control: Optional[Any], queue: Optional[Any]
    ) -> bool:
        """檢查檔案是否需要處理（EPUB）"""
        # EPUB 檔案本質也是 ZIP，但需檢查 mimetype
        if not zipfile.is_zipfile(str(file_path)):
            if queue:
                queue.put(
                    {
                        "type": "update_file_status",
                        "payload": {"status": f"無效檔案: {file_path.name}"},
                    }
                )
            return False
        # 可加強 mimetype 檢查（如需）
        return True

    def _get_file_size(self, file_path: Path) -> float:
        """取得檔案大小（KB）"""
        try:
            return file_path.stat().st_size / 1024 if file_path.exists() else 0.0
        except (OSError, AttributeError):
            return 0.0

    """EPUB 文件處理器（含標記和特殊邏輯）"""

    def __init__(
        self, config: CompressorConfig, global_control: Optional[GlobalControlProtocol]
    ):
        self.config = config
        self.image_compressor = ImageCompressor(config, global_control)
        self.marker = CompressionMarker()

    def process_file(
        self,
        file_path: Path,
        global_control: GlobalControlProtocol,
        queue: Optional[Any],
    ) -> Tuple[bool, int, int, float, float, float, int]:
        """處理 EPUB 檔案"""

        def send_update(msg_type: str, **payload):
            if queue:
                queue.put({"type": msg_type, "payload": payload})

        temp_dir = None
        processed_images = 0
        total_images = 0
        hit_rate_sum = 0.0
        original_size = self._get_file_size(file_path)
        compressed_size = original_size
        modified = False
        archive_config = self.config.get_archive_config(".epub")
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

            if global_control and global_control.wait_if_paused():
                raise InterruptedByUserError

            temp_dir = tempfile.mkdtemp()
            send_update("update_file_status", status="解壓縮 EPUB...")

            with zipfile.ZipFile(file_path, "r") as zip_ref:
                # 掃描圖片檔案
                image_list = [
                    name
                    for name in zip_ref.namelist()
                    if Path(name).suffix.lower()
                    in self.image_compressor.SUPPORTED_FORMATS
                ]
                total_images = len(image_list)
                self.log_debug(
                    f"EPUB {file_path.name} 發現 {total_images} 個圖片檔案")
                for img_name in image_list[:5]:  # 只記錄前5個圖片名稱
                    self.log_debug(f"  - {img_name}")
                if len(image_list) > 5:
                    self.log_debug(f"  ... 還有 {len(image_list) - 5} 個圖片")
                send_update("update_file_progress",
                            completed=0, total=total_images)
                zip_ref.extractall(temp_dir)

            if global_control and global_control.wait_if_paused():
                raise InterruptedByUserError

            send_update("update_file_status", status="EPUB 解壓完成，開始處理圖片...")

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
                # 如果被中斷但有修改，嘗試保存
                if modified:
                    self._repack_archive(
                        file_path,
                        files_to_repack,
                        temp_dir,
                        archive_config,
                        global_control,
                        queue,
                        modified=True,
                    )
                raise InterruptedByUserError

            if modified:
                # 過濾掉標記檔案，避免重複
                files_to_repack = [
                    f
                    for f in files_to_repack
                    if Path(f["arc"]).as_posix() != self.marker.MARKER_PATH
                ]
                self._repack_archive(
                    file_path,
                    files_to_repack,
                    temp_dir,
                    archive_config,
                    global_control,
                    queue,
                    modified=True,
                )
                compressed_size = self._get_file_size(file_path)
                send_update("update_file_status",
                            status=f"更新完成: {file_path.name}")
            else:
                send_update("update_file_status",
                            status=f"無需處理: {file_path.name}")

            send_update(
                "finish_file",
                success=True,
                processed_images=processed_images,
                total_images=total_images,
                original_size=original_size,
                compressed_size=compressed_size,
                hit_rate_sum=hit_rate_sum,
                successful_images=processed_images,
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
                original_size=original_size,
                compressed_size=original_size,
                hit_rate_sum=0.0,
                successful_images=0,
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
        except Exception as e:
            error_msg = str(e)
            if "Bad CRC-32" in error_msg:
                self.log_error(
                    f"EPUB {file_path.name} 損壞: {error_msg.split(':')[-1].strip()}")
            else:
                self.log_error(f"處理 EPUB {file_path.name} 時發生錯誤: {error_msg}")
            send_update(
                "finish_file",
                success=False,
                processed_images=0,
                total_images=total_images,
                original_size=original_size,
                compressed_size=original_size,
                hit_rate_sum=0.0,
                successful_images=0,
            )
            return False, 0, total_images, original_size, original_size, 0.0, 0
        finally:
            if temp_dir:
                shutil.rmtree(temp_dir, ignore_errors=True)
