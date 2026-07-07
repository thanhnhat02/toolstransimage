"""
Settings sidebar panel — AI mode, upscale target, export, post-processing sliders.
"""
import logging
from pathlib import Path

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSlider,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from src.core.gpu_detector import get_gpu_info
from src.core.settings import AppSettings

logger = logging.getLogger(__name__)

AI_MODES = [
    ("Real-ESRGAN (Fast & Reliable)",          "real_esrgan"),
    ("SwinIR (High Detail)",                   "swinir"),
    ("SUPIR (Photorealistic, 12GB+ VRAM)",     "supir"),
    ("SDXL Img2Img (Creative, 8GB+ VRAM)",     "sdxl"),
    ("ControlNet Tile (Ultra Detail, 10GB+)",  "controlnet"),
    ("Flux Fill (State-of-Art, 12GB+ VRAM)",   "flux_fill"),
    ("✨ Hybrid Mode (Recommended)",            "hybrid"),
]

UPSCALE_TARGETS = ["Original Size", "2K", "4K", "8K", "2×", "4×"]
EXPORT_FORMATS  = ["PNG (Lossless)", "JPEG", "WEBP"]


class SettingsPanel(QWidget):
    """Left sidebar with all processing settings."""

    settings_changed = Signal()

    def __init__(self, app_settings: AppSettings, parent=None):
        super().__init__(parent)
        self._settings = app_settings
        self._build_ui()
        self._load_saved_settings()

    # ------------------------------------------------------------------ #
    # Build UI
    # ------------------------------------------------------------------ #

    def _build_ui(self):
        self.setFixedWidth(280)
        self.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        # ── Scroll area ──────────────────────────────────────────────── #
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        scroll.setFrameShape(QScrollArea.NoFrame)

        inner_widget = QWidget()
        inner_widget.setObjectName("settings_inner")
        self._layout = QVBoxLayout(inner_widget)
        self._layout.setContentsMargins(12, 12, 12, 12)
        self._layout.setSpacing(12)

        self._build_gpu_info()
        self._build_ai_mode()
        self._build_upscale()
        self._build_export()
        self._build_face_options()
        self._build_postprocess()
        self._build_advanced()

        self._layout.addStretch()
        scroll.setWidget(inner_widget)
        outer.addWidget(scroll)

    # ── GPU Info Card ────────────────────────────────────────────────── #

    def _build_gpu_info(self):
        gpu = get_gpu_info()

        frame = QWidget()
        frame.setObjectName("gpu_card")
        frame.setStyleSheet("""
            #gpu_card {
                background: qlineargradient(x1:0,y1:0,x2:1,y2:1,
                    stop:0 #0D2137, stop:1 #0F1117);
                border: 1px solid #1F4A7E;
                border-radius: 8px;
                padding: 2px;
            }
        """)
        lay = QVBoxLayout(frame)
        lay.setContentsMargins(12, 10, 12, 10)
        lay.setSpacing(4)

        if gpu["available"]:
            icon_txt = "🚀 GPU Detected"
            name_txt = gpu["name"]
            vram_txt = f"{gpu['vram_gb']} GB VRAM  •  CUDA {gpu['cuda_version']}"
            color = "#56D364"
        else:
            icon_txt = "⚙️ CPU Mode"
            name_txt = "No CUDA GPU found"
            vram_txt = "Processing may be slow on CPU"
            color = "#F0883E"

        header = QLabel(icon_txt)
        header.setStyleSheet(f"color: {color}; font-weight: 700; font-size: 12px;")
        name_lbl = QLabel(name_txt)
        name_lbl.setStyleSheet("color: #C9D1D9; font-size: 12px; font-weight: 600;")
        name_lbl.setWordWrap(True)
        vram_lbl = QLabel(vram_txt)
        vram_lbl.setStyleSheet("color: #8B949E; font-size: 11px;")
        vram_lbl.setWordWrap(True)

        lay.addWidget(header)
        lay.addWidget(name_lbl)
        lay.addWidget(vram_lbl)
        self._layout.addWidget(frame)

    # ── AI Mode ──────────────────────────────────────────────────────── #

    def _build_ai_mode(self):
        grp = QGroupBox("AI Enhancement Engine")
        lay = QVBoxLayout(grp)
        lay.setSpacing(6)

        self.combo_mode = QComboBox()
        for label, _ in AI_MODES:
            self.combo_mode.addItem(label)
        self.combo_mode.setToolTip(
            "Select the AI model for upscaling.\n"
            "Real-ESRGAN is fast and works on all GPUs.\n"
            "Hybrid mode gives the best quality."
        )
        self.combo_mode.currentIndexChanged.connect(self._on_settings_changed)
        lay.addWidget(self.combo_mode)

        self._mode_info = QLabel()
        self._mode_info.setWordWrap(True)
        self._mode_info.setStyleSheet("color: #8B949E; font-size: 11px;")
        lay.addWidget(self._mode_info)
        self._update_mode_info(0)
        self.combo_mode.currentIndexChanged.connect(self._update_mode_info)

        self._layout.addWidget(grp)

    def _update_mode_info(self, idx: int):
        infos = [
            "Fast, great quality. Works on GPU ≥ 4 GB VRAM or CPU.",
            "Excellent detail recovery. Works on GPU ≥ 6 GB VRAM or CPU.",
            "Photorealistic restoration. Requires ≥ 12 GB VRAM.",
            "Creative texture generation. Requires ≥ 8 GB VRAM.",
            "Ultra-detail from tile conditioning. Requires ≥ 10 GB VRAM.",
            "State-of-the-art fill. Requires ≥ 12 GB VRAM.",
            "Best quality: Real-ESRGAN + optional SDXL texture pass.",
        ]
        self._mode_info.setText(infos[idx] if idx < len(infos) else "")

    # ── Upscale Target ────────────────────────────────────────────────── #

    def _build_upscale(self):
        grp = QGroupBox("Upscale Target")
        lay = QVBoxLayout(grp)
        lay.setSpacing(6)

        self.combo_upscale = QComboBox()
        for t in UPSCALE_TARGETS:
            self.combo_upscale.addItem(t)
        self.combo_upscale.setCurrentText("4K")
        self.combo_upscale.setToolTip(
            "Target output resolution.\n"
            "4K = 3840×2160 (recommended).\n"
            "4× = 4× original dimensions."
        )
        self.combo_upscale.currentIndexChanged.connect(self._on_settings_changed)
        lay.addWidget(self.combo_upscale)

        self._layout.addWidget(grp)

    # ── Export Format ─────────────────────────────────────────────────── #

    def _build_export(self):
        grp = QGroupBox("Export Format")
        lay = QVBoxLayout(grp)
        lay.setSpacing(6)

        self.combo_export = QComboBox()
        for f in EXPORT_FORMATS:
            self.combo_export.addItem(f)
        self.combo_export.setToolTip(
            "Output file format.\n"
            "PNG is lossless (largest file).\n"
            "WEBP offers good quality at smaller size."
        )
        self.combo_export.currentIndexChanged.connect(self._on_settings_changed)
        lay.addWidget(self.combo_export)

        self._layout.addWidget(grp)

    # ── Face & Restore Options ────────────────────────────────────────── #

    def _build_face_options(self):
        grp = QGroupBox("AI Restoration Options")
        lay = QVBoxLayout(grp)
        lay.setSpacing(6)

        self.chk_face = QCheckBox("Face Restoration (GFPGAN)")
        self.chk_face.setChecked(True)
        self.chk_face.setToolTip(
            "Automatically detect and enhance faces.\n"
            "Uses GFPGAN to restore eyes, skin, and hair.\n"
            "Auto-downloads model on first use."
        )
        self.chk_face.stateChanged.connect(self._on_settings_changed)

        self.chk_gpu = QCheckBox("Use GPU (CUDA)")
        self.chk_gpu.setChecked(True)
        self.chk_gpu.setToolTip(
            "Use NVIDIA GPU when available.\n"
            "Uncheck to force CPU-only mode."
        )
        self.chk_gpu.stateChanged.connect(self._on_settings_changed)

        self.chk_half = QCheckBox("Half Precision (FP16)")
        self.chk_half.setChecked(True)
        self.chk_half.setToolTip(
            "Use float16 for faster processing and lower VRAM.\n"
            "Requires Volta+ GPU (RTX / GTX 16xx+)."
        )
        self.chk_half.stateChanged.connect(self._on_settings_changed)

        lay.addWidget(self.chk_face)
        lay.addWidget(self.chk_gpu)
        lay.addWidget(self.chk_half)
        self._layout.addWidget(grp)

    # ── Post-Processing ───────────────────────────────────────────────── #

    def _build_postprocess(self):
        grp = QGroupBox("Post-Processing")
        lay = QVBoxLayout(grp)
        lay.setSpacing(10)

        self.chk_sharpen = QCheckBox("Adaptive Sharpen")
        self.chk_sharpen.setChecked(True)
        self.chk_sharpen.stateChanged.connect(self._on_settings_changed)

        self.sl_sharpen = self._make_slider("Sharpen Strength", 0, 100, 60, "sharpness")

        self.chk_contrast = QCheckBox("Local Contrast (CLAHE)")
        self.chk_contrast.setChecked(True)
        self.chk_contrast.stateChanged.connect(self._on_settings_changed)

        self.sl_contrast = self._make_slider("Contrast Strength", 0, 100, 40, "contrast")

        self.chk_denoise = QCheckBox("Smart Denoise")
        self.chk_denoise.setChecked(True)
        self.chk_denoise.stateChanged.connect(self._on_settings_changed)

        self.sl_denoise = self._make_slider("Denoise Strength", 0, 100, 50, "denoise")

        self.chk_edge = QCheckBox("Edge Enhancement")
        self.chk_edge.setChecked(True)
        self.chk_edge.stateChanged.connect(self._on_settings_changed)

        lay.addWidget(self.chk_sharpen)
        lay.addWidget(self.sl_sharpen["widget"])
        lay.addWidget(self.chk_contrast)
        lay.addWidget(self.sl_contrast["widget"])
        lay.addWidget(self.chk_denoise)
        lay.addWidget(self.sl_denoise["widget"])
        lay.addWidget(self.chk_edge)
        self._layout.addWidget(grp)

    def _make_slider(
        self, label: str, min_v: int, max_v: int, default: int, key: str
    ) -> dict:
        widget = QWidget()
        lay = QHBoxLayout(widget)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.setSpacing(6)

        lbl = QLabel(f"{default}%")
        lbl.setFixedWidth(36)
        lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        lbl.setStyleSheet("color: #58A6FF; font-size: 11px; font-weight: 600;")

        slider = QSlider(Qt.Horizontal)
        slider.setRange(min_v, max_v)
        slider.setValue(default)
        slider.valueChanged.connect(lambda v: lbl.setText(f"{v}%"))
        slider.valueChanged.connect(self._on_settings_changed)

        lay.addWidget(slider)
        lay.addWidget(lbl)
        return {"widget": widget, "slider": slider, "label": lbl}

    # ── Advanced ──────────────────────────────────────────────────────── #

    def _build_advanced(self):
        grp = QGroupBox("Advanced")
        lay = QFormLayout(grp)
        lay.setSpacing(8)

        self.combo_tile = QComboBox()
        for t in ["256", "512", "768", "1024"]:
            self.combo_tile.addItem(f"Tile size: {t}")
        self.combo_tile.setCurrentIndex(1)   # 512
        self.combo_tile.setToolTip(
            "Tile size for tiled inference.\n"
            "Smaller = less VRAM, slower.\n"
            "Larger = more VRAM, faster."
        )
        self.combo_tile.currentIndexChanged.connect(self._on_settings_changed)
        lay.addRow("", self.combo_tile)

        self._layout.addWidget(grp)

    # ------------------------------------------------------------------ #
    # Settings persistence
    # ------------------------------------------------------------------ #

    def _load_saved_settings(self):
        s = self._settings

        # AI mode
        mode_key = s.ai_mode
        for i, (_, key) in enumerate(AI_MODES):
            if key == mode_key:
                self.combo_mode.setCurrentIndex(i)
                break

        # Upscale
        target = s.upscale_target
        for i, t in enumerate(UPSCALE_TARGETS):
            if t == target or t.rstrip() == target:
                self.combo_upscale.setCurrentIndex(i)
                break

        # Export
        fmt = s.export_format
        for i, f in enumerate(EXPORT_FORMATS):
            if fmt.upper() in f.upper():
                self.combo_export.setCurrentIndex(i)
                break

        # Checkboxes
        self.chk_face.setChecked(s.get("use_face_restore", True))
        self.chk_gpu.setChecked(s.get("use_gpu", True))
        self.chk_half.setChecked(s.get("half_precision", True))
        self.chk_sharpen.setChecked(s.get("use_sharpen", True))
        self.chk_contrast.setChecked(s.get("use_local_contrast", True))
        self.chk_denoise.setChecked(s.get("use_denoise", True))
        self.chk_edge.setChecked(s.get("use_edge_enhance", True))

        # Sliders
        self.sl_sharpen["slider"].setValue(int(s.get("sharpen_strength", 0.6) * 100))
        self.sl_contrast["slider"].setValue(int(s.get("contrast_strength", 0.4) * 100))
        self.sl_denoise["slider"].setValue(int(s.get("denoise_strength", 0.5) * 100))

    def save_settings(self):
        s = self._settings
        s.ai_mode = AI_MODES[self.combo_mode.currentIndex()][1]
        s.upscale_target = self.get_upscale_target()
        s.export_format = self.get_export_format()
        s.set("use_face_restore", self.chk_face.isChecked())
        s.set("use_gpu", self.chk_gpu.isChecked())
        s.set("half_precision", self.chk_half.isChecked())
        s.set("use_sharpen", self.chk_sharpen.isChecked())
        s.set("use_local_contrast", self.chk_contrast.isChecked())
        s.set("use_denoise", self.chk_denoise.isChecked())
        s.set("use_edge_enhance", self.chk_edge.isChecked())
        s.set("sharpen_strength", self.sl_sharpen["slider"].value() / 100)
        s.set("contrast_strength", self.sl_contrast["slider"].value() / 100)
        s.set("denoise_strength", self.sl_denoise["slider"].value() / 100)
        s.sync()

    def _on_settings_changed(self, *_):
        self.save_settings()
        self.settings_changed.emit()

    # ------------------------------------------------------------------ #
    # Getters for main window
    # ------------------------------------------------------------------ #

    def get_ai_mode(self) -> str:
        return AI_MODES[self.combo_mode.currentIndex()][1]

    def get_upscale_target(self) -> str:
        raw = self.combo_upscale.currentText()
        return raw.replace("×", "x").replace("Original Size", "original")

    def get_export_format(self) -> str:
        raw = self.combo_export.currentText()
        if "PNG" in raw:
            return "PNG"
        if "JPEG" in raw:
            return "JPEG"
        return "WEBP"

    def get_tile_size(self) -> int:
        t = self.combo_tile.currentText().split()[-1]
        return int(t)
