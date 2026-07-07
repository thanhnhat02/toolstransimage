"""
QThread-based worker for batch image processing.
Emits Qt signals for real-time progress updates in the GUI.
"""
import logging
import time
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import QThread, Signal

from src.pipeline.processor import ImageProcessor, ProcessingConfig, ProcessingResult

logger = logging.getLogger(__name__)


class EnhancementWorker(QThread):
    """
    Runs the image enhancement pipeline in a background thread.

    Signals:
        started_loading(str)        - Model loading begins
        model_status(str)           - Model loading status message
        image_started(int, str)     - (index, filename) Processing started
        image_done(ProcessingResult)- Single image completed
        image_failed(int, str)      - (index, error_message)
        progress(int, int)          - (current, total) count
        batch_done(list)            - All results when finished
        log_message(str)            - General log messages for UI
        eta_update(float, float)    - (elapsed_secs, eta_secs)
    """

    # ── Signals ─────────────────────────────────────────────────────── #
    started_loading = Signal(str)
    model_status = Signal(str)
    image_started = Signal(int, str)
    image_done = Signal(object)
    image_failed = Signal(int, str)
    progress = Signal(int, int)
    batch_done = Signal(list)
    log_message = Signal(str)
    eta_update = Signal(float, float)

    def __init__(
        self,
        image_paths: List[Path],
        output_dir: Path,
        config: ProcessingConfig,
        parent=None,
    ):
        super().__init__(parent)
        self._paths = image_paths
        self._output_dir = output_dir
        self._config = config
        self._processor: Optional[ImageProcessor] = None
        self._paused = False
        self._stopped = False
        self._results: List[ProcessingResult] = []

    # ------------------------------------------------------------------ #
    # Control methods (called from main thread)
    # ------------------------------------------------------------------ #

    def pause(self) -> None:
        self._paused = True
        logger.info("Batch processing paused")

    def resume(self) -> None:
        self._paused = False
        logger.info("Batch processing resumed")

    def stop(self) -> None:
        self._stopped = True
        self._paused = False
        logger.info("Batch processing stop requested")

    @property
    def is_paused(self) -> bool:
        return self._paused

    # ------------------------------------------------------------------ #
    # QThread entry point
    # ------------------------------------------------------------------ #

    def run(self) -> None:
        total = len(self._paths)
        self._results = []

        # ── Load models ────────────────────────────────────────────── #
        self.started_loading.emit("Loading AI models …")
        self._processor = ImageProcessor(self._config)
        try:
            self._processor.load_models(progress_cb=lambda msg: self.model_status.emit(msg))
        except Exception as e:
            self.log_message.emit(f"❌ Model load failed: {e}")
            self.batch_done.emit([])
            return

        batch_start = time.perf_counter()

        # ── Process each image ─────────────────────────────────────── #
        for idx, path in enumerate(self._paths):
            # Check stop signal
            if self._stopped:
                self.log_message.emit("⏹ Stopped by user")
                break

            # Handle pause
            while self._paused and not self._stopped:
                self.msleep(200)

            self.image_started.emit(idx, path.name)
            self.log_message.emit(f"Processing [{idx+1}/{total}]: {path.name}")

            result = self._processor.process_image(
                input_path=path,
                output_dir=self._output_dir,
                progress_cb=lambda msg: self.log_message.emit(f"  {msg}"),
            )
            self._results.append(result)

            if result.success:
                self.image_done.emit(result)
                self.log_message.emit(
                    f"  ✓ Done in {result.elapsed_seconds:.1f}s → "
                    f"{result.output_path.name if result.output_path else '?'}"
                )
            else:
                self.image_failed.emit(idx, result.error or "Unknown error")
                self.log_message.emit(f"  ✗ Failed: {result.error}")

            self.progress.emit(idx + 1, total)

            # ETA calculation
            elapsed = time.perf_counter() - batch_start
            done = idx + 1
            remaining = total - done
            if done > 0 and remaining > 0:
                avg_time = elapsed / done
                eta = avg_time * remaining
                self.eta_update.emit(elapsed, eta)

        # ── Cleanup ────────────────────────────────────────────────── #
        try:
            self._processor.unload_models()
        except Exception:
            pass

        self.batch_done.emit(self._results)
