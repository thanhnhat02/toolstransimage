"""
Main application window.
Integrates all panels, handles input/output selection, starts batch processing.
"""
import logging
from pathlib import Path
from typing import List, Optional

from PySide6.QtCore import Qt, QTimer, Slot
from PySide6.QtGui import QAction, QFont, QIcon, QKeySequence
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QSizePolicy,
    QSplitter,
    QStatusBar,
    QToolBar,
    QVBoxLayout,
    QWidget,
)

from src.core.image_utils import scan_folder, is_supported
from src.core.settings import AppSettings
from src.gui.panels.progress_panel import ProgressPanel
from src.gui.panels.settings_panel import SettingsPanel
from src.gui.widgets.file_queue import FileQueueWidget, FileStatus
from src.gui.widgets.image_preview import ImagePreviewWidget
from src.pipeline.processor import ProcessingConfig
from src.workers.enhancement_worker import EnhancementWorker

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Primary application window with:
    - Left sidebar: AI settings
    - Center: Image preview (before / after)
    - Right: File queue
    - Bottom: Progress panel
    - Toolbar: Input / output / start controls
    """

    def __init__(self, app_settings: AppSettings):
        super().__init__()
        self._settings = app_settings
        self._worker: Optional[EnhancementWorker] = None
        self._image_paths: List[Path] = []
        self._output_dir: Optional[Path] = None
        self._processing = False

        self._build_ui()
        self._connect_signals()
        self._restore_geometry()

    # ------------------------------------------------------------------ #
    # Build UI
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        self.setWindowTitle("AI Image Enhancer  —  Professional Edition")
        self.setMinimumSize(1200, 780)

        # ── Central widget ────────────────────────────────────────────── #
        central = QWidget()
        self.setCentralWidget(central)
        root_lay = QVBoxLayout(central)
        root_lay.setContentsMargins(0, 0, 0, 0)
        root_lay.setSpacing(0)

        # ── Header bar ────────────────────────────────────────────────── #
        self._build_header(root_lay)

        # ── Input / Output bar ────────────────────────────────────────── #
        self._build_io_bar(root_lay)

        # ── Main content (splitter) ───────────────────────────────────── #
        self._build_content(root_lay)

        # ── Progress panel at bottom ──────────────────────────────────── #
        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        sep.setStyleSheet("color: #21262D;")
        root_lay.addWidget(sep)

        self._progress_panel = ProgressPanel()
        root_lay.addWidget(self._progress_panel)

        # ── Status bar ────────────────────────────────────────────────── #
        self._status = QStatusBar()
        self.setStatusBar(self._status)
        self._status_lbl = QLabel("Ready  •  Select images and click Start")
        self._status.addWidget(self._status_lbl)

        # ── Menu bar ──────────────────────────────────────────────────── #
        self._build_menu()

    def _build_header(self, parent_lay: QVBoxLayout):
        header = QWidget()
        header.setObjectName("app_header")
        header.setFixedHeight(64)
        header.setStyleSheet("""
            #app_header {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #0D1117, stop:0.5 #161B22, stop:1 #0D1117);
                border-bottom: 1px solid #21262D;
            }
        """)

        h_lay = QHBoxLayout(header)
        h_lay.setContentsMargins(16, 0, 16, 0)
        h_lay.setSpacing(12)

        # Logo / title
        title = QLabel("🤖 AI Image Enhancer")
        title.setObjectName("title_label")
        title.setStyleSheet("""
            font-size: 20px;
            font-weight: 800;
            background: transparent;
            color: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                stop:0 #58A6FF, stop:1 #A5D6FF);
        """)

        subtitle = QLabel(
            "Professional Image Upscaling  •  Real-ESRGAN · SwinIR · SDXL · Face Restore"
        )
        subtitle.setObjectName("subtitle_label")

        v = QVBoxLayout()
        v.setSpacing(2)
        v.addWidget(title)
        v.addWidget(subtitle)

        h_lay.addLayout(v)
        h_lay.addStretch()

        # Quick stats
        self._hdr_gpu = QLabel("⚙️ Detecting …")
        self._hdr_gpu.setStyleSheet("color: #8B949E; font-size: 12px;")
        h_lay.addWidget(self._hdr_gpu)
        QTimer.singleShot(100, self._update_gpu_label)

        parent_lay.addWidget(header)

    def _update_gpu_label(self):
        from src.core.gpu_detector import get_gpu_info
        gpu = get_gpu_info()
        if gpu["available"]:
            self._hdr_gpu.setText(f"🚀 {gpu['name']}  {gpu['vram_gb']} GB VRAM")
            self._hdr_gpu.setStyleSheet("color: #56D364; font-size: 12px;")
        else:
            self._hdr_gpu.setText("⚙️ CPU Mode")
            self._hdr_gpu.setStyleSheet("color: #F0883E; font-size: 12px;")

    def _build_io_bar(self, parent_lay: QVBoxLayout):
        bar = QWidget()
        bar.setObjectName("io_bar")
        bar.setStyleSheet("""
            #io_bar {
                background: #161B22;
                border-bottom: 1px solid #21262D;
            }
        """)
        bar.setFixedHeight(56)

        lay = QHBoxLayout(bar)
        lay.setContentsMargins(16, 8, 16, 8)
        lay.setSpacing(8)

        # ── Input controls ──────────────────────────────────────────── #
        self.btn_single  = QPushButton("🖼  Add Image")
        self.btn_folder  = QPushButton("📁  Add Folder")
        self.btn_clear_q = QPushButton("✕  Clear")

        for btn in (self.btn_single, self.btn_folder):
            btn.setObjectName("btn_icon")
            btn.setFixedHeight(36)
        self.btn_clear_q.setObjectName("btn_icon")
        self.btn_clear_q.setFixedHeight(36)

        self._input_path_lbl = QLineEdit()
        self._input_path_lbl.setReadOnly(True)
        self._input_path_lbl.setPlaceholderText("No input selected …")
        self._input_path_lbl.setFixedHeight(36)

        lay.addWidget(QLabel("Input:"))
        lay.addWidget(self.btn_single)
        lay.addWidget(self.btn_folder)
        lay.addWidget(self._input_path_lbl, 1)
        lay.addWidget(self.btn_clear_q)

        # Separator
        sep = QFrame()
        sep.setFrameShape(QFrame.VLine)
        sep.setStyleSheet("color: #30363D;")
        lay.addWidget(sep)

        # ── Output controls ─────────────────────────────────────────── #
        self.btn_output = QPushButton("📂  Output Folder")
        self.btn_output.setObjectName("btn_icon")
        self.btn_output.setFixedHeight(36)

        self._output_path_lbl = QLineEdit()
        self._output_path_lbl.setReadOnly(True)
        self._output_path_lbl.setPlaceholderText("No output folder selected …")
        self._output_path_lbl.setFixedHeight(36)
        out_folder = self._settings.last_output_folder
        if out_folder:
            self._output_path_lbl.setText(out_folder)
            self._output_dir = Path(out_folder)

        lay.addWidget(QLabel("Output:"))
        lay.addWidget(self.btn_output)
        lay.addWidget(self._output_path_lbl, 1)

        # Separator
        sep2 = QFrame()
        sep2.setFrameShape(QFrame.VLine)
        sep2.setStyleSheet("color: #30363D;")
        lay.addWidget(sep2)

        # ── Start button ────────────────────────────────────────────── #
        self.btn_start = QPushButton("▶  Start Processing")
        self.btn_start.setObjectName("btn_primary")
        self.btn_start.setFixedHeight(40)
        self.btn_start.setFixedWidth(180)
        self.btn_start.setEnabled(False)
        lay.addWidget(self.btn_start)

        parent_lay.addWidget(bar)

    def _build_content(self, parent_lay: QVBoxLayout):
        splitter = QSplitter(Qt.Horizontal)
        splitter.setHandleWidth(1)

        # ── Left: Settings panel ─────────────────────────────────────── #
        self._settings_panel = SettingsPanel(self._settings)
        splitter.addWidget(self._settings_panel)

        # ── Center: Preview ──────────────────────────────────────────── #
        center = QWidget()
        center_lay = QVBoxLayout(center)
        center_lay.setContentsMargins(8, 8, 8, 8)
        center_lay.setSpacing(4)

        preview_label = QLabel("Preview (drag divider to compare Before / After)")
        preview_label.setStyleSheet("color: #8B949E; font-size: 11px;")
        preview_label.setAlignment(Qt.AlignCenter)

        self._preview = ImagePreviewWidget()
        center_lay.addWidget(preview_label)
        center_lay.addWidget(self._preview, 1)
        splitter.addWidget(center)

        # ── Right: File queue ────────────────────────────────────────── #
        right = QWidget()
        right.setFixedWidth(300)
        right_lay = QVBoxLayout(right)
        right_lay.setContentsMargins(8, 8, 8, 8)
        right_lay.setSpacing(6)

        self._queue = FileQueueWidget()
        right_lay.addWidget(self._queue)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setStretchFactor(2, 0)

        parent_lay.addWidget(splitter, 1)

    def _build_menu(self):
        menubar = self.menuBar()

        # File
        file_menu = menubar.addMenu("File")
        act_img  = QAction("Add Image(s) …", self)
        act_fol  = QAction("Add Folder …",   self)
        act_quit = QAction("Quit",            self)
        act_quit.setShortcut(QKeySequence.Quit)
        act_img.triggered.connect(self._select_single_images)
        act_fol.triggered.connect(self._select_folder)
        act_quit.triggered.connect(self.close)
        file_menu.addAction(act_img)
        file_menu.addAction(act_fol)
        file_menu.addSeparator()
        file_menu.addAction(act_quit)

        # Help
        help_menu = menubar.addMenu("Help")
        act_about = QAction("About", self)
        act_about.triggered.connect(self._show_about)
        help_menu.addAction(act_about)

    # ------------------------------------------------------------------ #
    # Signal connections
    # ------------------------------------------------------------------ #

    def _connect_signals(self):
        self.btn_single.clicked.connect(self._select_single_images)
        self.btn_folder.clicked.connect(self._select_folder)
        self.btn_clear_q.clicked.connect(self._clear_queue)
        self.btn_output.clicked.connect(self._select_output_folder)
        self.btn_start.clicked.connect(self._start_processing)

        pp = self._progress_panel
        pp.btn_pause.clicked.connect(self._pause_processing)
        pp.btn_resume.clicked.connect(self._resume_processing)
        pp.btn_stop.clicked.connect(self._stop_processing)

    # ------------------------------------------------------------------ #
    # Input / Output selection
    # ------------------------------------------------------------------ #

    def _select_single_images(self):
        paths, _ = QFileDialog.getOpenFileNames(
            self,
            "Select Image(s)",
            self._settings.last_input_folder,
            "Images (*.jpg *.jpeg *.png *.webp *.bmp *.tiff *.tif)",
        )
        if paths:
            new_paths = [Path(p) for p in paths if is_supported(Path(p))]
            self._add_images(new_paths)
            if new_paths:
                self._settings.last_input_folder = str(new_paths[0].parent)
                self._input_path_lbl.setText(
                    str(new_paths[0].parent)
                    if len(new_paths) > 1
                    else str(new_paths[0])
                )
                self._preview.set_before(new_paths[0])

    def _select_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Image Folder",
            self._settings.last_input_folder,
        )
        if folder:
            folder_path = Path(folder)
            images = scan_folder(folder_path)
            self._add_images(images)
            if images:
                self._settings.last_input_folder = str(folder_path)
                self._input_path_lbl.setText(str(folder_path))
                self._preview.set_before(images[0])

    def _add_images(self, paths: List[Path]):
        # Deduplicate
        existing = {str(p) for p in self._image_paths}
        new = [p for p in paths if str(p) not in existing]
        self._image_paths.extend(new)
        self._queue.set_images(self._image_paths)
        self._refresh_start_button()
        self._update_status()

    def _clear_queue(self):
        self._image_paths = []
        self._queue.clear_queue()
        self._preview.clear()
        self._input_path_lbl.clear()
        self._refresh_start_button()
        self._update_status()

    def _select_output_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Output Folder",
            self._settings.last_output_folder,
        )
        if folder:
            self._output_dir = Path(folder)
            self._settings.last_output_folder = folder
            self._output_path_lbl.setText(folder)
            self._refresh_start_button()

    # ------------------------------------------------------------------ #
    # Processing control
    # ------------------------------------------------------------------ #

    def _build_config(self) -> ProcessingConfig:
        sp = self._settings_panel
        return ProcessingConfig(
            ai_mode=sp.get_ai_mode(),
            upscale_target=sp.get_upscale_target(),
            export_format=sp.get_export_format(),
            use_gpu=sp.chk_gpu.isChecked(),
            use_face_restore=sp.chk_face.isChecked(),
            use_denoise=sp.chk_denoise.isChecked(),
            use_sharpen=sp.chk_sharpen.isChecked(),
            use_local_contrast=sp.chk_contrast.isChecked(),
            use_edge_enhance=sp.chk_edge.isChecked(),
            denoise_strength=sp.sl_denoise["slider"].value() / 100,
            sharpen_strength=sp.sl_sharpen["slider"].value() / 100,
            contrast_strength=sp.sl_contrast["slider"].value() / 100,
            half_precision=sp.chk_half.isChecked(),
            tile_size=sp.get_tile_size(),
            output_dir=self._output_dir,
            models_dir=Path.home() / ".cache" / "ai_enhancer" / "weights",
        )

    def _start_processing(self):
        if not self._image_paths:
            QMessageBox.warning(self, "No Images", "Please select images first.")
            return
        if not self._output_dir:
            QMessageBox.warning(self, "No Output", "Please select an output folder.")
            return

        self._output_dir.mkdir(parents=True, exist_ok=True)
        config = self._build_config()

        self._worker = EnhancementWorker(
            image_paths=self._image_paths,
            output_dir=self._output_dir,
            config=config,
        )

        # ── Connect worker signals ──────────────────────────────────── #
        self._worker.model_status.connect(self._progress_panel.append_log)
        self._worker.log_message.connect(self._progress_panel.append_log)
        self._worker.progress.connect(self._on_progress)
        self._worker.image_started.connect(self._on_image_started)
        self._worker.image_done.connect(self._on_image_done)
        self._worker.image_failed.connect(self._on_image_failed)
        self._worker.eta_update.connect(self._progress_panel.on_eta)
        self._worker.batch_done.connect(self._on_batch_done)

        self._processing = True
        self._progress_panel.reset(len(self._image_paths))
        self.btn_start.setEnabled(False)
        self._update_status(processing=True)
        self._worker.start()

    def _pause_processing(self):
        if self._worker:
            self._worker.pause()
            self._progress_panel.mark_paused()

    def _resume_processing(self):
        if self._worker:
            self._worker.resume()
            self._progress_panel.mark_resumed()

    def _stop_processing(self):
        if self._worker:
            self._worker.stop()
            self._progress_panel.mark_stopped()

    # ------------------------------------------------------------------ #
    # Worker signal handlers
    # ------------------------------------------------------------------ #

    @Slot(int, int)
    def _on_progress(self, done: int, total: int):
        self._progress_panel.on_progress(done, total)

    @Slot(int, str)
    def _on_image_started(self, idx: int, name: str):
        self._queue.set_status(idx, FileStatus.RUNNING, "processing …")
        self._progress_panel.mark_started(idx, name)

    @Slot(object)
    def _on_image_done(self, result):
        idx = self._image_paths.index(result.input_path) if result.input_path in self._image_paths else -1
        elapsed_str = f"{result.elapsed_seconds:.1f}s"
        self._queue.set_status(idx, FileStatus.DONE, elapsed_str)

        # Update preview with result
        if result.output_path and result.output_path.exists():
            self._preview.set_after(result.output_path)

    @Slot(int, str)
    def _on_image_failed(self, idx: int, error: str):
        self._queue.set_status(idx, FileStatus.FAILED, "failed")

    @Slot(list)
    def _on_batch_done(self, results: list):
        self._processing = False
        self._progress_panel.mark_done()
        self.btn_start.setEnabled(True)
        self._update_status()

        done = sum(1 for r in results if r.success)
        failed = len(results) - done

        msg = f"✅ Batch complete: {done} succeeded"
        if failed:
            msg += f", {failed} failed"
        msg += f"  →  {self._output_dir}"

        self._status_lbl.setText(msg)
        self._progress_panel.append_log(f"\n{msg}")

        if done > 0 and self._output_dir:
            # Open output folder
            import subprocess
            subprocess.Popen(["xdg-open", str(self._output_dir)])

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    def _refresh_start_button(self):
        can_start = (
            len(self._image_paths) > 0
            and self._output_dir is not None
            and not self._processing
        )
        self.btn_start.setEnabled(can_start)

    def _update_status(self, processing: bool = False):
        n = len(self._image_paths)
        if processing:
            self._status_lbl.setText(
                f"Processing {n} image(s) → {self._output_dir} …"
            )
        elif n == 0:
            self._status_lbl.setText("Ready  •  Select images and click Start")
        else:
            out_str = str(self._output_dir) if self._output_dir else "no output folder"
            self._status_lbl.setText(f"{n} image(s) ready  •  Output: {out_str}")

    def _show_about(self):
        QMessageBox.about(
            self,
            "About AI Image Enhancer",
            "<h3>AI Image Enhancer — Professional Edition</h3>"
            "<p>Upscale, restore, and enhance images using state-of-the-art AI models.</p>"
            "<ul>"
            "<li>Real-ESRGAN  •  SwinIR  •  SUPIR</li>"
            "<li>Stable Diffusion XL  •  ControlNet  •  Flux</li>"
            "<li>GFPGAN Face Restoration</li>"
            "<li>OpenCV Adaptive Post-Processing</li>"
            "</ul>"
            "<p>Runs entirely offline. No cloud. No paid APIs.</p>",
        )

    def _restore_geometry(self):
        geom = self._settings.get("window_geometry")
        if geom:
            try:
                self.restoreGeometry(geom)
            except Exception:
                self.resize(1400, 860)
        else:
            self.resize(1400, 860)

    def closeEvent(self, event):
        if self._worker and self._worker.isRunning():
            self._worker.stop()
            self._worker.wait(3000)
        self._settings.set("window_geometry", self.saveGeometry())
        self._settings.sync()
        event.accept()
