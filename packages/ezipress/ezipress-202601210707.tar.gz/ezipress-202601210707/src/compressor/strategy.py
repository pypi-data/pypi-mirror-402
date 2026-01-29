"""
壓縮策略
"""

import io
import functools
from typing import Tuple, Optional, Dict, Any

from ..config import CompressorConfig
from ..utils.logger import LoggerMixin
from .exceptions import InterruptedByUserError, DependencyError
from ..typing import GlobalControlProtocol


def check_compression_dependencies():
    """檢查壓縮相關依賴"""
    missing_deps = []

    try:
        import numpy as np
    except ImportError:
        missing_deps.append("numpy")

    try:
        import skfuzzy as fuzz
        from skfuzzy import control as ctrl
    except ImportError:
        missing_deps.append("scikit-fuzzy")

    if missing_deps:
        raise DependencyError(f"缺少壓縮策略依賴: {', '.join(missing_deps)}")


class CompressionStrategy(LoggerMixin):
    """壓縮策略實現 (V_a11 邏輯)"""

    def __init__(
        self,
        config: CompressorConfig,
        global_control: Optional[GlobalControlProtocol] = None,
    ):
        self.config = config
        self.global_control = global_control
        self._fuzzy_cache = {}

    def compress_to_target(
        self,
        img,
        image_path: str,
        output_path: str,
        save_format: str,
        original_size_kb: float,
        target_size_kb: float,
        initial_quality: int,
        global_control: GlobalControlProtocol,
        queue: Optional[Any],
    ) -> Tuple[bool, float, float]:
        """壓縮圖片到目標大小"""
        from PIL import Image

        processed_img = self._preprocess_image(img, save_format)

        if save_format == "PNG":
            return self._compress_png_strategy(
                processed_img,
                output_path,
                target_size_kb,
                initial_quality,
                global_control,
                queue,
            )
        else:
            return self._compress_jpeg_webp_strategy(
                processed_img,
                img.size,
                output_path,
                save_format,
                original_size_kb,
                target_size_kb,
                initial_quality,
                global_control,
                queue,
            )

    def _check_should_exit(self, global_control: GlobalControlProtocol):
        """檢查是否應該退出"""
        if global_control and global_control.wait_if_paused():
            raise InterruptedByUserError

    def _preprocess_image(self, img, save_format: str):
        """預處理圖片格式"""
        from PIL import Image

        if save_format != "JPEG":
            return img.copy()

        # JPEG 格式處理
        if img.mode in ("RGBA", "LA", "P"):
            if img.mode == "P" and "transparency" not in img.info:
                # 調色板模式但無透明度
                return img.convert("RGB")

            # 處理透明度
            background = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")

            mask = img.split()[-1] if img.mode in ("RGBA", "LA") else None
            if mask and mask.getextrema()[0] < 255:
                background.paste(img, mask=mask)
                return background
            else:
                return img.convert("RGB")
        elif img.mode != "RGB":
            return img.convert("RGB")

        return img.copy()

    def _compress_png_strategy(
        self,
        img,
        output_path: str,
        target_size_kb: float,
        initial_quality: int,
        global_control: GlobalControlProtocol,
        queue: Optional[Any],
    ) -> Tuple[bool, float, float]:
        """PNG 專用壓縮策略"""

        def send_update(msg_type: str, **payload):
            if queue:
                queue.put({"type": msg_type, "payload": payload})

        best_result = {"buffer": None, "size": float("inf")}
        best_under_target = {"buffer": None, "size": 0}
        tolerance = max(8, target_size_kb * 0.05)
        total_iterations = 0
        successful_iterations = 0

        fixed_quality = 60
        low_scale, high_scale = 0.1, 1.0
        last_size = None
        stagnant_count = 0
        max_iterations = 12

        send_update("update_iteration", current=0, total=max_iterations)

        for iteration in range(max_iterations):
            self._check_should_exit(global_control)
            total_iterations += 1

            current_scale = (low_scale + high_scale) / 2
            buffer, actual_size_kb, width, height = self._perform_compression_attempt(
                img, img.size, fixed_quality, current_scale, "PNG"
            )

            if actual_size_kb == float("inf"):
                high_scale = current_scale
                continue

            # 更新統計
            if abs(actual_size_kb - target_size_kb) <= tolerance:
                successful_iterations += 1

            hit_rate = (
                (successful_iterations / total_iterations) * 100
                if total_iterations > 0
                else 0
            )

            send_update(
                "update_compression_params",
                quality=fixed_quality,
                scale=current_scale,
                current_size=actual_size_kb,
            )
            send_update(
                "update_iteration",
                current=iteration + 1,
                total=max_iterations,
                hit_rate=hit_rate,
            )

            # 檢查是否停滯
            if last_size is not None and abs(actual_size_kb - last_size) < 1.0:
                stagnant_count += 1
                if stagnant_count >= 2:
                    break
            else:
                stagnant_count = 0
            last_size = actual_size_kb

            # 更新最佳結果
            current_params = {
                "q": fixed_quality,
                "s": current_scale,
                "w": width,
                "h": height,
            }

            if abs(actual_size_kb - target_size_kb) < abs(
                best_result.get("size", float("inf")) - target_size_kb
            ):
                best_result = {
                    "buffer": buffer,
                    "size": actual_size_kb,
                    "params": current_params,
                }

            if (
                actual_size_kb <= target_size_kb
                and actual_size_kb > best_under_target.get("size", 0)
            ):
                best_under_target = {
                    "buffer": buffer,
                    "size": actual_size_kb,
                    "params": current_params,
                }

            # 調整搜尋範圍
            if actual_size_kb <= target_size_kb:
                low_scale = current_scale
            else:
                high_scale = current_scale

            # 檢查收斂條件
            if (
                abs(actual_size_kb - target_size_kb) <= tolerance
                or high_scale - low_scale < 0.005
            ):
                break

        # 選擇最終結果
        final_result = (
            best_under_target if best_under_target.get("buffer") else best_result
        )
        final_hit_rate = (
            (successful_iterations / total_iterations) * 100
            if total_iterations > 0
            else 0
        )

        if final_result.get("buffer"):
            try:
                with open(output_path, "wb") as f:
                    f.write(final_result["buffer"].getvalue())
                return True, final_result["size"], final_hit_rate
            except OSError as e:
                self.log_error(f"無法寫入檔案 {output_path}: {e}")

        return False, 0, 0

    def _compress_jpeg_webp_strategy(
        self,
        img,
        original_size: tuple,
        output_path: str,
        save_format: str,
        original_size_kb: float,
        target_size_kb: float,
        initial_quality: int,
        global_control: GlobalControlProtocol,
        queue: Optional[Any],
    ) -> Tuple[bool, float, float]:
        """JPEG/WEBP 壓縮策略"""

        def send_update(msg_type: str, **payload):
            if queue:
                queue.put({"type": msg_type, "payload": payload})

        best_result = {"buffer": None, "size": float("inf")}
        best_under_target = {"buffer": None, "size": 0}
        tolerance = max(8, target_size_kb * 0.05)
        total_iterations = 0
        successful_iterations = 0

        min_quality, max_quality = 20, initial_quality
        params = self._calculate_initial_params(
            original_size_kb, target_size_kb, quality_range=(min_quality, max_quality)
        )
        current_quality = params["quality"]

        max_phase1_iterations = 8
        max_total_iterations = max_phase1_iterations + 5
        low_scale, high_scale = 0.1, 1.0

        send_update("update_iteration", current=0, total=max_total_iterations)

        # Phase 1: Scale optimization
        for iteration in range(max_phase1_iterations):
            self._check_should_exit(global_control)
            total_iterations += 1

            current_scale = (low_scale + high_scale) / 2
            buffer, actual_size_kb, width, height = self._perform_compression_attempt(
                img, original_size, current_quality, current_scale, save_format
            )

            if actual_size_kb == float("inf"):
                high_scale = current_scale
                continue

            if abs(actual_size_kb - target_size_kb) <= tolerance:
                successful_iterations += 1

            hit_rate = (
                (successful_iterations / total_iterations) * 100
                if total_iterations > 0
                else 0
            )

            send_update(
                "update_compression_params",
                quality=current_quality,
                scale=current_scale,
                current_size=actual_size_kb,
            )
            send_update(
                "update_iteration",
                current=iteration + 1,
                total=max_total_iterations,
                hit_rate=hit_rate,
            )

            # 更新最佳結果
            current_params = {
                "q": current_quality,
                "s": current_scale,
                "w": width,
                "h": height,
            }

            if abs(actual_size_kb - target_size_kb) < abs(
                best_result.get("size", float("inf")) - target_size_kb
            ):
                best_result = {
                    "buffer": buffer,
                    "size": actual_size_kb,
                    "params": current_params,
                }

            if (
                actual_size_kb <= target_size_kb
                and actual_size_kb > best_under_target.get("size", 0)
            ):
                best_under_target = {
                    "buffer": buffer,
                    "size": actual_size_kb,
                    "params": current_params,
                }

            # 調整搜尋範圍
            if actual_size_kb <= target_size_kb:
                low_scale = current_scale
            else:
                high_scale = current_scale

            if high_scale - low_scale < 0.01:
                break

        # Phase 2: Quality fine-tuning (如果需要)
        if (
            best_under_target.get("buffer") is None
            and total_iterations < max_total_iterations
        ):
            best_scale = best_result.get("params", {}).get("s", 1.0)
            for q_offset in [-5, -10, -15, 5, 10]:
                if total_iterations >= max_total_iterations:
                    break

                self._check_should_exit(global_control)
                total_iterations += 1

                test_quality = max(
                    min_quality, min(max_quality, current_quality + q_offset)
                )
                (
                    buffer,
                    actual_size_kb,
                    width,
                    height,
                ) = self._perform_compression_attempt(
                    img, original_size, test_quality, best_scale, save_format
                )

                if actual_size_kb != float("inf"):
                    if abs(actual_size_kb - target_size_kb) <= tolerance:
                        successful_iterations += 1

                    hit_rate = (
                        (successful_iterations / total_iterations) * 100
                        if total_iterations > 0
                        else 0
                    )
                    send_update(
                        "update_compression_params",
                        quality=test_quality,
                        scale=best_scale,
                        current_size=actual_size_kb,
                    )
                    send_update(
                        "update_iteration",
                        current=max_phase1_iterations
                        + (total_iterations - max_phase1_iterations),
                        total=max_total_iterations,
                        hit_rate=hit_rate,
                    )

                    # 更新結果
                    if (
                        actual_size_kb <= target_size_kb
                        and actual_size_kb > best_under_target.get("size", 0)
                    ):
                        best_under_target = {
                            "buffer": buffer,
                            "size": actual_size_kb,
                            "params": {
                                "q": test_quality,
                                "s": best_scale,
                                "w": width,
                                "h": height,
                            },
                        }

        # 選擇最終結果
        final_result = (
            best_under_target if best_under_target.get("buffer") else best_result
        )
        final_hit_rate = (
            (successful_iterations / total_iterations) * 100
            if total_iterations > 0
            else 0
        )

        if final_result.get("buffer"):
            try:
                with open(output_path, "wb") as f:
                    f.write(final_result["buffer"].getvalue())
                return True, final_result["size"], final_hit_rate
            except OSError as e:
                self.log_error(f"無法寫入檔案 {output_path}: {e}")

        return False, original_size_kb, 0

    def _perform_compression_attempt(
        self,
        img,
        original_dimensions: tuple,
        quality: float,
        scale: float,
        save_format: str,
    ) -> Tuple[io.BytesIO, float, int, int]:
        """執行單次壓縮嘗試"""
        from PIL import Image

        new_width = int(original_dimensions[0] * scale)
        new_height = int(original_dimensions[1] * scale)

        if new_width < 1 or new_height < 1:
            return io.BytesIO(), float("inf"), 0, 0

        try:
            # 調整圖片大小
            if (new_width, new_height) != img.size:
                resized_img = img.resize(
                    (new_width, new_height), Image.Resampling.LANCZOS
                )
            else:
                resized_img = img

            # 壓縮
            buffer = io.BytesIO()
            save_kwargs = {"optimize": True}

            if save_format in ("JPEG", "WEBP"):
                save_kwargs["quality"] = int(quality)
                if save_format == "JPEG":
                    save_kwargs["progressive"] = True
            elif save_format == "PNG":
                save_kwargs["compress_level"] = min(9, max(1, round(quality / 100 * 9)))

            resized_img.save(buffer, format=save_format, **save_kwargs)

            return buffer, len(buffer.getvalue()) / 1024, new_width, new_height

        except Exception as e:
            self.log_debug(f"壓縮嘗試失敗: {e}")
            return io.BytesIO(), float("inf"), new_width, new_height

    @functools.lru_cache(maxsize=128)
    def _calculate_initial_params(
        self,
        original_size_kb: float,
        target_size_kb: float,
        quality_range: Tuple[int, int],
    ) -> Dict[str, float]:
        """使用模糊邏輯計算初始參數"""
        min_q, max_q = quality_range

        if target_size_kb >= original_size_kb:
            return {"quality": max_q, "scale": 1.0}

        cache_key = (original_size_kb, target_size_kb, quality_range)
        if cache_key in self._fuzzy_cache:
            return self._fuzzy_cache[cache_key]

        try:
            # 檢查依賴
            check_compression_dependencies()

            import numpy as np
            import skfuzzy as fuzz
            from skfuzzy import control as ctrl

            # 定義模糊系統
            universe_size = np.arange(0, 10241, 1)
            universe_ratio = np.arange(0, 1.01, 0.01)
            universe_quality = np.arange(min_q, max_q + 1, 1)
            universe_scale = np.arange(0.1, 1.01, 0.01)

            img_size = ctrl.Antecedent(universe_size, "size")
            comp_ratio = ctrl.Antecedent(universe_ratio, "ratio")
            out_quality = ctrl.Consequent(universe_quality, "quality")
            out_scale = ctrl.Consequent(universe_scale, "scale")

            # 定義隸屬函數
            img_size["small"] = fuzz.trimf(universe_size, [0, 512, 1024])
            img_size["medium"] = fuzz.trimf(universe_size, [512, 2048, 4096])
            img_size["large"] = fuzz.trapmf(universe_size, [3072, 6144, 10240, 10240])

            comp_ratio["low"] = fuzz.trimf(universe_ratio, [0, 0, 0.3])
            comp_ratio["medium"] = fuzz.trimf(universe_ratio, [0.2, 0.5, 0.8])
            comp_ratio["high"] = fuzz.trimf(universe_ratio, [0.7, 1, 1])

            out_quality["low"] = fuzz.trimf(
                universe_quality, [min_q, min_q + 15, min_q + 30]
            )
            out_quality["medium"] = fuzz.trimf(
                universe_quality, [min_q + 25, (min_q + max_q) / 2, max_q - 10]
            )
            out_quality["high"] = fuzz.trimf(
                universe_quality, [max_q - 15, max_q - 5, max_q]
            )

            out_scale["low"] = fuzz.trimf(universe_scale, [0.1, 0.3, 0.5])
            out_scale["medium"] = fuzz.trimf(universe_scale, [0.4, 0.7, 0.9])
            out_scale["high"] = fuzz.trimf(universe_scale, [0.8, 1, 1])

            # 定義規則
            rules = [
                ctrl.Rule(
                    img_size["large"] | comp_ratio["low"],
                    (out_quality["low"], out_scale["low"]),
                ),
                ctrl.Rule(
                    img_size["medium"] & comp_ratio["medium"],
                    (out_quality["medium"], out_scale["medium"]),
                ),
                ctrl.Rule(
                    img_size["small"] | comp_ratio["high"],
                    (out_quality["high"], out_scale["high"]),
                ),
                ctrl.Rule(
                    img_size["medium"] & comp_ratio["low"],
                    (out_quality["low"], out_scale["medium"]),
                ),
                ctrl.Rule(
                    img_size["large"] & comp_ratio["medium"],
                    (out_quality["medium"], out_scale["low"]),
                ),
            ]

            # 建立控制系統
            compression_ctrl = ctrl.ControlSystem(rules)
            compression_sim = ctrl.ControlSystemSimulation(compression_ctrl)

            # 計算結果
            compression_sim.input["size"] = min(original_size_kb, 10240)
            compression_sim.input["ratio"] = (
                target_size_kb / original_size_kb if original_size_kb > 0 else 1.0
            )
            compression_sim.compute()

            result = {
                "quality": float(compression_sim.output["quality"]),
                "scale": float(compression_sim.output["scale"]),
            }

            self._fuzzy_cache[cache_key] = result
            return result

        except Exception as e:
            self.log_debug(f"模糊邏輯計算失敗，使用簡化策略: {e}")
            # 簡化策略
            ratio = target_size_kb / original_size_kb
            if ratio > 0.8:
                result = {"quality": max_q * 0.9, "scale": 1.0}
            elif ratio > 0.5:
                result = {"quality": (min_q + max_q) / 2, "scale": 0.9}
            else:
                result = {"quality": min_q + 20, "scale": 0.7}

            self._fuzzy_cache[cache_key] = result
            return result
