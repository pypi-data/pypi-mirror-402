"""
no-progress/批次模式專用互動控制
"""

import sys
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import Optional

from ..config import CompressorConfig
from ..utils.logger import LoggerMixin


class BatchController(LoggerMixin):
    """批次模式控制器"""

    def __init__(self, config: CompressorConfig):
        self.config = config
        self.global_control = None  # 批次模式是非互動式的

    def run_processing(self) -> int:
        """執行批次處理"""
        self.log_info(f"交互式進度顯示已禁用。使用傳統輸出模式，執行緒數: {self.config.workers}")

        # 預先檢查和過濾檔案
        actual_files = self._pre_check_files()
        if not actual_files:
            self.log_info("經過篩選，沒有檔案需要處理。")
            return 0

        self.log_info(
            f"\n將使用 {self.config.workers} 個工作程序處理 {len(actual_files)} 個檔案...")

        success_count = 0
        failed_count = 0
        successful_files = []
        failed_files = []

        try:
            with ProcessPoolExecutor(max_workers=self.config.workers) as executor:
                # 提交所有任務
                future_to_file = {
                    executor.submit(
                        self._process_archive_worker_task, self.config, str(f)
                    ): f
                    for f in actual_files
                }

                # 處理完成的任務
                for future in as_completed(future_to_file):
                    file = future_to_file[future]
                    try:
                        result = future.result()
                        if len(result) == 7:  # 正常結果
                            success, processed, total, orig, comp, _, _ = result
                            if success:
                                success_count += 1
                                successful_files.append(file.name)
                                self.log_info(
                                    f"--- ✅ 完成: {file.name} "
                                    + f"(圖片: {processed}/{total}, "
                                    + f"{orig:.1f}KB -> {comp:.1f}KB) ---"
                                )
                            else:
                                failed_count += 1
                                failed_files.append(file.name)
                                self.log_warning(
                                    f"--- ❌ 失敗: {file.name} "
                                    + f"(圖片: {processed}/{total}, "
                                    + f"{orig:.1f}KB -> {comp:.1f}KB) ---"
                                )
                        # 錯誤結果格式 (從 worker 異常中返回)
                        elif len(result) == 8 and result[7] == "ERROR_RESULT":
                            success, processed, total, orig, comp, error_msg, stack_trace, marker = result
                            failed_count += 1
                            failed_files.append(file.name)
                            self.log_error(f"--- ❌ 處理檔案 {file.name} 失敗 ---")
                            if error_msg:
                                self.log_error(f"錯誤訊息: {error_msg}")
                            if stack_trace:
                                self.log_debug(f"詳細堆疊追蹤:\n{stack_trace}")
                        else:
                            failed_count += 1
                            failed_files.append(file.name)
                            self.log_error(
                                f"--- ❌ 處理檔案 {file.name} 時返回未知格式的結果 ---")
                    except Exception as e:
                        failed_count += 1
                        failed_files.append(file.name)
                        self.log_exception(
                            f"--- ❌ 處理檔案 {file.name} 時發生嚴重錯誤: {e} ---")

        except KeyboardInterrupt:
            self.log_warning("批次處理被用戶中斷。")
            return 130

        # 顯示總結
        total_files = success_count + failed_count
        self.log_info(f"\n批次處理完成。總計: {total_files} 個檔案")
        self.log_info(f"成功: {success_count}, 失敗: {failed_count}")

        if successful_files:
            self.log_info("成功的檔案:")
            for filename in successful_files:
                self.log_info(f"  ✅ {filename}")

        if failed_files:
            self.log_info("失敗的檔案:")
            for filename in failed_files:
                self.log_info(f"  ❌ {filename}")

        return 0 if failed_count == 0 else 1

    def _pre_check_files(self):
        """預先檢查檔案"""
        actual_files = []
        self.log_info(f"找到 {len(self.config.files_to_process)} 個檔案。正在預先檢查...")

        for file_path in self.config.files_to_process:
            if not file_path.exists():
                self.log_warning(f"檔案不存在，跳過: {file_path}")
                continue

            if self._should_skip_file(file_path):
                continue

            actual_files.append(file_path)

        return actual_files

    def _should_skip_file(self, file_path) -> bool:
        """檢查是否應跳過檔案"""
        # 檢查 EPUB 壓縮標記
        if not self.config.force and file_path.suffix.lower() == ".epub":
            from ..archive.marker import CompressionMarker

            marker = CompressionMarker()
            marker_info = marker.check_compression_marker(str(file_path))
            if marker_info.get("is_compressed"):
                if self.config.skip_compressed:
                    version = marker_info.get("data", {}).get("version", "未知")
                    self.log_info(f"跳過已壓縮的檔案: {file_path.name} (v{version})")
                    return True
        return False

    @staticmethod
    def _process_archive_worker_task(config: CompressorConfig, file_path_str: str):
        """工作進程任務"""
        import traceback
        from pathlib import Path
        from ..main import CompressorMain
        from ..utils.logger import setup_logging, get_logger

        # 為每個工作進程設定獨立的日誌記錄器
        setup_logging(level="DEBUG" if config.debug else "INFO")
        logger = get_logger(f"worker.{Path(file_path_str).stem}")

        file_path = Path(file_path_str)

        try:
            main_instance = CompressorMain(config)
            handler = main_instance.get_handler_for_file(file_path)
            # 批次模式：global_control 和 queue 都是 None
            return handler.process_file(file_path, None, None)
        except Exception as e:
            error_msg = str(e)
            stack_trace = traceback.format_exc()
            logger.exception(f"工作進程處理檔案 {file_path.name} 時發生未預期的錯誤")

            # 返回詳細的錯誤資訊
            original_size = 0.0
            try:
                original_size = (
                    file_path.stat().st_size / 1024 if file_path.exists() else 0.0
                )
            except (OSError, AttributeError):
                pass
            # 返回擴展的錯誤結果格式: (success, processed, total, orig, comp, error_msg, stack_trace, error_marker)
            return False, 0, 0, original_size, original_size, error_msg, stack_trace, "ERROR_RESULT"

    def cleanup(self):
        """清理資源（批次模式通常不需要特殊清理）"""
        pass

    def exit(self):
        """外部呼叫的退出方法（批次模式可能需要終止執行緒池）"""
        pass
