"""
Application settings management using QSettings for persistence across sessions.
"""
import logging
from pathlib import Path
from typing import Any

from PySide6.QtCore import QSettings

logger = logging.getLogger(__name__)

APP_NAME = "AIImageEnhancer"
ORG_NAME = "AIEnhancerTeam"


class AppSettings:
    """
    Persistent settings wrapper around QSettings.
    All settings are stored in the system's native config store.
    """

    _DEFAULTS: dict[str, Any] = {
        # Paths
        "last_input_folder": str(Path.home()),
        "last_output_folder": str(Path.home() / "Enhanced"),
        # Processing
        "ai_mode": "real_esrgan",
        "upscale_target": "4K",
        "export_format": "PNG",
        "use_gpu": True,
        "use_face_restore": True,
        "use_denoise": True,
        "use_sharpen": True,
        "use_local_contrast": True,
        "denoise_strength": 0.5,
        "sharpen_strength": 0.6,
        "contrast_strength": 0.4,
        # UI
        "window_geometry": None,
        "splitter_state": None,
        # Advanced
        "max_workers": 1,
        "half_precision": True,
        "tile_size": 512,
    }

    def __init__(self):
        self._qs = QSettings(ORG_NAME, APP_NAME)
        logger.debug(f"Settings file: {self._qs.fileName()}")

    def get(self, key: str, default: Any = None) -> Any:
        """Retrieve a setting value with fallback to default."""
        fallback = default if default is not None else self._DEFAULTS.get(key)
        val = self._qs.value(key, fallback)
        # QSettings sometimes returns strings for bools
        if isinstance(fallback, bool) and isinstance(val, str):
            val = val.lower() in ("true", "1", "yes")
        if isinstance(fallback, int) and isinstance(val, str):
            try:
                val = int(val)
            except ValueError:
                val = fallback
        if isinstance(fallback, float) and isinstance(val, str):
            try:
                val = float(val)
            except ValueError:
                val = fallback
        return val

    def set(self, key: str, value: Any) -> None:
        """Persist a setting value."""
        self._qs.setValue(key, value)

    def sync(self) -> None:
        """Force flush settings to disk."""
        self._qs.sync()

    def reset_to_defaults(self) -> None:
        """Clear all settings and restore defaults."""
        self._qs.clear()
        logger.info("Settings reset to defaults")

    # ------------------------------------------------------------------ #
    # Convenience properties
    # ------------------------------------------------------------------ #

    @property
    def last_input_folder(self) -> str:
        return self.get("last_input_folder")

    @last_input_folder.setter
    def last_input_folder(self, v: str):
        self.set("last_input_folder", v)

    @property
    def last_output_folder(self) -> str:
        return self.get("last_output_folder")

    @last_output_folder.setter
    def last_output_folder(self, v: str):
        self.set("last_output_folder", v)

    @property
    def ai_mode(self) -> str:
        return self.get("ai_mode")

    @ai_mode.setter
    def ai_mode(self, v: str):
        self.set("ai_mode", v)

    @property
    def upscale_target(self) -> str:
        return self.get("upscale_target")

    @upscale_target.setter
    def upscale_target(self, v: str):
        self.set("upscale_target", v)

    @property
    def export_format(self) -> str:
        return self.get("export_format")

    @export_format.setter
    def export_format(self, v: str):
        self.set("export_format", v)

    @property
    def use_gpu(self) -> bool:
        return self.get("use_gpu")

    @use_gpu.setter
    def use_gpu(self, v: bool):
        self.set("use_gpu", v)
