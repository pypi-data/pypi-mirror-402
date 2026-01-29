"""
圖片壓縮核心
"""

import os
import shutil
from pathlib import Path
from typing import Optional, Tuple, List, Dict, Any, Set

from ..config import CompressorConfig
from ..utils.logger import LoggerMixin
from .strategy import CompressionStrategy
from .exceptions import InterruptedByUserError, DependencyError
from ..typing import GlobalControlProtocol


def check_dependencies():
    """檢查必要的依賴"""
    missing_deps = []

    try:
        import PIL
    except ImportError:
        missing_deps.append("Pillow")

    if missing_deps:
        raise DependencyError(
            f"缺少必要的依賴: {', '.join(missing_deps)}。請執行: pip install {' '.join(missing_deps)}"
        )


class ImageCompressor(LoggerMixin):
    """圖片壓縮器"""

    SUPPORTED_FORMATS: Set[str] = {".png", ".jpg", ".jpeg", ".webp"}
    EPUB_SKIP_EXTS: Set[str] = {
        ".html",
        ".xhtml",
        ".css",
        ".opf",
        ".ncx",
        ".xml",
        ".txt",
    }

    def __init__(
        self,
        config: CompressorConfig,
        global_control: Optional[GlobalControlProtocol] = None,
    ):
        check_dependencies()
        self.config = config
        self.global_control = global_control
        self.strategy = CompressionStrategy(config, global_control)
        self._file_size_cache: Dict[str, float] = {}

    def process_directory(
        self,
        temp_dir: str,
        compression_params: dict,
        archive_config: dict,
        global_control: GlobalControlProtocol,
        queue: Optional[Any],
        total_images_in_archive: int,
    ) -> Tuple[List[Dict], int, bool, int, float, float, float]:
        """處理目錄中的所有檔案"""

        def send_update(msg_type: str, **payload):
            if queue:
                queue.put({"type": msg_type, "payload": payload})

        files_to_repack = []
        processed_images_succeeded = 0
        modified = False
        total_size_before = 0.0
        total_size_after = 0.0
        total_hit_rate_sum = 0.0
        images_processed_so_far = 0

        is_epub = archive_config.get("is_epub", False)
        temp_path = Path(temp_dir)

        # 使用生成器來節省記憶體
        all_files = self._get_files_iterator(temp_path)

        for idx, file_path in enumerate(all_files):
            if global_control and idx % 10 == 0:
                if global_control.wait_if_paused():
                    raise InterruptedByUserError

            if is_epub and file_path.name == "mimetype":
                continue

            relative_path = file_path.relative_to(temp_path)
            current_size_kb = self._get_file_size_cached(file_path)
            total_size_before += current_size_kb
            final_size_kb = current_size_kb

            # 處理圖片檔案
            if self._is_image_file(file_path, is_epub=is_epub):
                if self._should_compress_image(current_size_kb, compression_params):
                    save_format, output_path = self._determine_output_format(
                        file_path,
                        relative_path,
                        current_size_kb,
                        archive_config,
                        temp_dir,
                    )

                    success, final_size_kb, hit_rate = self.compress_image_to_target(
                        str(file_path),
                        str(output_path),
                        save_format,
                        compression_params["target_size"],
                        compression_params.get("quality", 95),
                        global_control,
                        queue,
                    )

                    if success:
                        processed_images_succeeded += 1
                        total_hit_rate_sum += hit_rate
                        modified = True

                        # 清理原始檔案
                        self._cleanup_original_file(file_path, output_path)

                    files_to_repack.append(
                        {
                            "src": str(output_path),
                            "arc": relative_path.with_suffix(
                                output_path.suffix
                            ).as_posix(),
                        }
                    )

                    images_processed_so_far += 1
                    send_update(
                        "update_file_progress",
                        completed=images_processed_so_far,
                        total=total_images_in_archive,
                    )

                    if global_control and global_control.should_exit:
                        send_update("update_file_status",
                                    status="用戶請求退出，停止處理目錄...")
                        raise InterruptedByUserError
                else:
                    send_update(
                        "update_file_status",
                        status=f"跳過小圖: {file_path.name} ({self._format_size(current_size_kb)})",
                    )
                    files_to_repack.append(
                        {"src": str(file_path),
                         "arc": relative_path.as_posix()}
                    )
            else:
                files_to_repack.append(
                    {"src": str(file_path), "arc": relative_path.as_posix()}
                )

            total_size_after += final_size_kb

        return (
            files_to_repack,
            processed_images_succeeded,
            modified,
            total_images_in_archive,
            total_size_before,
            total_size_after,
            total_hit_rate_sum,
        )

    def compress_image_to_target(
        self,
        image_path: str,
        output_path: str,
        save_format: str,
        target_size_kb: float,
        initial_quality: int,
        global_control: GlobalControlProtocol,
        queue: Optional[Any],
    ) -> Tuple[bool, float, float]:
        """壓縮圖片到目標大小"""

        def send_update(msg_type: str, **payload):
            if queue:
                queue.put({"type": msg_type, "payload": payload})

        image_name = os.path.basename(image_path)
        original_size_kb = self._get_file_size_cached(Path(image_path))

        try:
            send_update(
                "start_image",
                image_name=image_name,
                original_size_kb=original_size_kb,
                target_size_kb=target_size_kb,
            )

            # 如果原圖已經小於等於目標大小，直接複製
            if target_size_kb >= original_size_kb:
                shutil.copy2(image_path, output_path)
                self.log_debug(
                    f"圖片 {image_name}: {original_size_kb:.1f}KB (小於目標 {target_size_kb:.1f}KB，跳過壓縮)")
                send_update(
                    "finish_image", success=True, final_size_kb=original_size_kb
                )
                return True, original_size_kb, 100.0

            from PIL import Image

            with Image.open(image_path) as img:
                success, final_size_kb, hit_rate = self.strategy.compress_to_target(
                    img,
                    image_path,
                    output_path,
                    save_format,
                    original_size_kb,
                    target_size_kb,
                    initial_quality,
                    global_control,
                    queue,
                )

            send_update(
                "finish_image",
                success=success,
                final_size_kb=final_size_kb if success else None,
            )

            # 非progress模式的fallback輸出
            if not queue and success:
                ratio = (
                    (1 - final_size_kb / original_size_kb) * 100
                    if original_size_kb > 0
                    else 0
                )
                self.log_info(
                    f"✓ 壓縮完成: {original_size_kb:.1f}KB -> {final_size_kb:.1f}KB (壓縮率: {ratio:.1f}%)"
                )
                self.log_debug(
                    f"圖片 {image_name}: {original_size_kb:.1f}KB -> {final_size_kb:.1f}KB (品質: {hit_rate:.1f}%)"
                )
            elif not queue:
                self.log_warning("  ✗ 壓縮失敗或跳過。")

            return success, final_size_kb, hit_rate

        except InterruptedByUserError:
            message = f"用戶已取消壓縮圖片 {image_name}。"
            send_update("finish_image", success=False, message=message)
            return False, original_size_kb, 0
        except Exception:
            self.log_exception(f"壓縮圖片 {image_name} 時發生未預期的錯誤")
            send_update("finish_image", success=False)
            return False, original_size_kb, 0

    def _get_files_iterator(self, temp_path: Path):
        """取得檔案迭代器，按路徑排序"""
        try:
            return sorted(temp_path.rglob("*"), key=lambda p: p.as_posix())
        except (OSError, PermissionError) as e:
            self.log_warning(f"無法列舉目錄 {temp_path}: {e}")
            return []

    def _get_file_size_cached(self, file_path: Path) -> float:
        """帶快取的檔案大小取得"""
        file_str = str(file_path)
        if file_str not in self._file_size_cache:
            try:
                self._file_size_cache[file_str] = file_path.stat(
                ).st_size / 1024
            except (OSError, FileNotFoundError):
                self._file_size_cache[file_str] = 0.0
        return self._file_size_cache[file_str]

    def _should_compress_image(
        self, current_size_kb: float, compression_params: dict
    ) -> bool:
        """判斷是否應該壓縮圖片"""
        return compression_params.get(
            "target_size"
        ) is not None and current_size_kb >= compression_params.get("min_size", 0)

    def _cleanup_original_file(self, original_path: Path, output_path: Path):
        """清理原始檔案"""
        if original_path != output_path and original_path.exists():
            try:
                original_path.unlink()
            except OSError as e:
                self.log_warning(f"無法刪除原始檔案 {original_path}: {e}")

    def _is_image_file(self, file_path: Path, is_epub: bool = False) -> bool:
        """判斷檔案是否為圖片"""
        if not file_path.is_file():
            return False

        if not is_epub:
            return file_path.suffix.lower() in self.SUPPORTED_FORMATS

        # EPUB 需要更仔細的檢查
        if file_path.suffix.lower() in self.EPUB_SKIP_EXTS:
            return False

        # 對於 EPUB，嘗試開啟檔案來確認是否為圖片
        try:
            from PIL import Image

            with Image.open(file_path) as img:
                img.verify()
            return True
        except Exception:
            return False

    def _determine_output_format(
        self,
        file_path: Path,
        relative_path: Path,
        current_size_kb: float,
        archive_config: dict,
        temp_dir: str,
    ) -> Tuple[str, Path]:
        """決定輸出格式和路徑"""
        original_format = self._get_image_format(file_path)
        save_format = original_format
        output_path = file_path

        # 只有非 EPUB 檔案才進行格式轉換
        if not archive_config.get("is_epub", False):
            if original_format == "PNG" and current_size_kb > archive_config.get(
                "png_to_jpg_threshold", float("inf")
            ):
                save_format = "JPEG"
                output_path = file_path.with_suffix(".jpg")
            elif original_format == "WEBP" and current_size_kb > archive_config.get(
                "webp_to_jpg_threshold", float("inf")
            ):
                save_format = "JPEG"
                output_path = file_path.with_suffix(".jpg")

        return save_format, output_path

    def _get_image_format(self, file_path: Path) -> str:
        """取得圖片格式"""
        try:
            from PIL import Image

            with Image.open(file_path) as img:
                return img.format or "UNKNOWN"
        except Exception:
            return "UNKNOWN"

    def _format_size(self, size_kb: float) -> str:
        """格式化檔案大小"""
        if size_kb < 1024:
            return f"{size_kb:.1f}KB"
        elif size_kb < 1024 * 1024:
            return f"{size_kb/1024:.1f}MB"
        else:
            return f"{size_kb/(1024*1024):.1f}GB"
