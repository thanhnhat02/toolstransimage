"""
GFPGAN / CodeFormer face restoration model.
Automatically detects and restores faces in enhanced images.

Priority:
  1. CodeFormer (newer, higher quality)
  2. GFPGAN v1.4 (fallback)
"""
import logging
from pathlib import Path
from typing import Optional

import cv2
import numpy as np
from PIL import Image

from .base_model import BaseModel, ModelNotAvailableError

logger = logging.getLogger(__name__)

GFPGAN_URL = (
    "https://github.com/TencentARC/GFPGAN/releases/download/"
    "v1.3.4/GFPGANv1.4.pth"
)
CODEFORMER_URL = (
    "https://github.com/sczhou/CodeFormer/releases/download/"
    "v0.1.0/codeformer.pth"
)


class FaceRestoreModel(BaseModel):
    """
    Face restoration using GFPGAN.
    Detects faces automatically and blends restoration with the background.
    """

    def __init__(
        self,
        device: str = "cpu",
        half_precision: bool = False,
        models_dir: Optional[Path] = None,
        weight: float = 0.5,   # 0 = strong restore, 1 = original
    ):
        super().__init__(device, half_precision)
        self._models_dir = models_dir or (Path.home() / ".cache" / "ai_enhancer" / "weights")
        self._weight = weight   # fidelity weight (for CodeFormer)
        self._restorer = None

    @property
    def model_name(self) -> str:
        return "GFPGAN v1.4 Face Restore"

    def is_available(self) -> bool:
        try:
            import gfpgan  # noqa: F401
            return True
        except ImportError:
            return False

    def load(self) -> None:
        if self._loaded:
            return
        if not self.is_available():
            raise ModelNotAvailableError(
                "gfpgan package not installed.\n"
                "Run: pip install gfpgan"
            )

        from gfpgan import GFPGANer

        self._models_dir.mkdir(parents=True, exist_ok=True)
        weight_file = self._models_dir / "GFPGANv1.4.pth"

        if not weight_file.exists():
            self.logger.info("Downloading GFPGAN v1.4 weights …")
            import urllib.request
            urllib.request.urlretrieve(GFPGAN_URL, str(weight_file))

        gpu_id = 0 if self.device == "cuda" else None

        self._restorer = GFPGANer(
            model_path=str(weight_file),
            upscale=1,
            arch="clean",
            channel_multiplier=2,
            gpu_id=gpu_id,
        )

        self._loaded = True
        self.logger.info(f"GFPGAN loaded on {self.device.upper()}")

    def enhance(
        self,
        image: Image.Image,
        scale: float = 1.0,
        tile_size: int = 512,
    ) -> Image.Image:
        """
        Detect and restore faces in the image.
        Returns the image with enhanced faces blended back in.
        """
        self.ensure_loaded()

        # PIL RGB → OpenCV BGR
        img_bgr = cv2.cvtColor(np.array(image), cv2.COLOR_RGB2BGR)

        _, _, restored_img = self._restorer.enhance(
            img_bgr,
            has_aligned=False,
            only_center_face=False,
            paste_back=True,
            weight=self._weight,
        )

        if restored_img is None:
            # No faces detected — return original
            self.logger.debug("No faces detected — skipping face restoration")
            return image

        return Image.fromarray(cv2.cvtColor(restored_img, cv2.COLOR_BGR2RGB))

    def unload(self) -> None:
        self._restorer = None
        self._loaded = False
        self._free_vram()
        self.logger.info("FaceRestoreModel unloaded")
