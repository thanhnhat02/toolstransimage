"""
Real-ESRGAN model wrapper.
Uses the official realesrgan package for high-quality 4x upscaling.
Supports x2, x4 general and anime models.
"""
import logging
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

from .base_model import BaseModel, ModelNotAvailableError

logger = logging.getLogger(__name__)

# Model URLs (HuggingFace / GitHub releases)
MODEL_URLS = {
    "RealESRGAN_x4plus": (
        "https://github.com/xinntao/Real-ESRGAN/releases/download/"
        "v0.1.0/RealESRGAN_x4plus.pth"
    ),
    "RealESRGAN_x2plus": (
        "https://github.com/xinntao/Real-ESRGAN/releases/download/"
        "v0.2.1/RealESRGAN_x2plus.pth"
    ),
    "RealESRNet_x4plus": (
        "https://github.com/xinntao/Real-ESRGAN/releases/download/"
        "v0.1.1/RealESRNet_x4plus.pth"
    ),
    "RealESRGAN_x4plus_anime_6B": (
        "https://github.com/xinntao/Real-ESRGAN/releases/download/"
        "v0.2.2.4/RealESRGAN_x4plus_anime_6B.pth"
    ),
}


class RealESRGANModel(BaseModel):
    """
    Real-ESRGAN 4x / 2x upscaling with tiled inference to reduce VRAM usage.
    Falls back gracefully when the realesrgan package is not installed.
    """

    def __init__(
        self,
        device: str = "cpu",
        half_precision: bool = False,
        model_name_key: str = "RealESRGAN_x4plus",
        models_dir: Optional[Path] = None,
        scale: int = 4,
    ):
        super().__init__(device, half_precision)
        self._model_name_key = model_name_key
        self._models_dir = models_dir or (Path.home() / ".cache" / "ai_enhancer" / "weights")
        self._scale = scale
        self._upsampler = None

    # ------------------------------------------------------------------ #
    # BaseModel interface
    # ------------------------------------------------------------------ #

    @property
    def model_name(self) -> str:
        return f"Real-ESRGAN ({self._model_name_key})"

    def is_available(self) -> bool:
        try:
            import realesrgan  # noqa: F401
            import basicsr  # noqa: F401
            return True
        except ImportError:
            return False

    def load(self) -> None:
        if self._loaded:
            return

        if not self.is_available():
            raise ModelNotAvailableError(
                "realesrgan package is not installed.\n"
                "Run: pip install realesrgan basicsr"
            )

        from basicsr.archs.rrdbnet_arch import RRDBNet
        from realesrgan import RealESRGANer

        self._models_dir.mkdir(parents=True, exist_ok=True)
        weight_file = self._models_dir / f"{self._model_name_key}.pth"

        # ── Download weights if missing ──────────────────────────────── #
        if not weight_file.exists():
            self.logger.info(f"Downloading {self._model_name_key} weights …")
            self._download_weights(weight_file)

        # ── Build network architecture ───────────────────────────────── #
        if "anime_6B" in self._model_name_key:
            model_net = RRDBNet(
                num_in_ch=3, num_out_ch=3, num_feat=64,
                num_block=6, num_grow_ch=32, scale=4,
            )
        else:
            model_net = RRDBNet(
                num_in_ch=3, num_out_ch=3, num_feat=64,
                num_block=23, num_grow_ch=32, scale=self._scale,
            )

        use_half = self.half_precision and self.device == "cuda"
        gpu_id = 0 if self.device == "cuda" else None

        self._upsampler = RealESRGANer(
            scale=self._scale,
            model_path=str(weight_file),
            model=model_net,
            tile=512,
            tile_pad=10,
            pre_pad=0,
            half=use_half,
            gpu_id=gpu_id,
        )

        self._loaded = True
        self.logger.info(f"Real-ESRGAN loaded on {self.device.upper()}")

    def enhance(
        self,
        image: Image.Image,
        scale: float = 4.0,
        tile_size: int = 512,
    ) -> Image.Image:
        self.ensure_loaded()

        import cv2

        # PIL RGB → OpenCV BGR
        img_bgr = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        # Run Real-ESRGAN
        output, _ = self._upsampler.enhance(img_bgr, outscale=scale)

        # OpenCV BGR → PIL RGB
        return Image.fromarray(cv2.cvtColor(output, cv2.COLOR_BGR2RGB))

    def unload(self) -> None:
        self._upsampler = None
        self._loaded = False
        self._free_vram()
        self.logger.info("Real-ESRGAN unloaded")

    # ------------------------------------------------------------------ #
    # Internal helpers
    # ------------------------------------------------------------------ #

    def _download_weights(self, dest: Path) -> None:
        url = MODEL_URLS.get(self._model_name_key)
        if not url:
            raise ModelNotAvailableError(f"No URL for model: {self._model_name_key}")

        import urllib.request

        self.logger.info(f"Downloading from {url}")
        urllib.request.urlretrieve(url, str(dest))
        self.logger.info(f"Weights saved → {dest}")
