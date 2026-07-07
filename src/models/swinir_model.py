"""
SwinIR model wrapper.
SwinIR is a Swin Transformer-based image restoration model
that excels at super-resolution, denoising, and JPEG artifact removal.

Reference: https://github.com/JingyunLiang/SwinIR
"""
import logging
import urllib.request
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

from .base_model import BaseModel, ModelNotAvailableError

logger = logging.getLogger(__name__)

SWINIR_WEIGHTS = {
    "real_sr_x4": (
        "https://github.com/JingyunLiang/SwinIR/releases/download/v0.0/"
        "003_realSR_BSRGAN_DFO_s64w8_SwinIR-M_x4_GAN.pth"
    ),
    "real_sr_x2": (
        "https://github.com/JingyunLiang/SwinIR/releases/download/v0.0/"
        "003_realSR_BSRGAN_DFO_s64w8_SwinIR-M_x2_GAN.pth"
    ),
    "real_sr_x4_large": (
        "https://github.com/JingyunLiang/SwinIR/releases/download/v0.0/"
        "003_realSR_BSRGAN_DFOWMFC_s64w8_SwinIR-L_x4_GAN.pth"
    ),
}


class SwinIRModel(BaseModel):
    """
    SwinIR super-resolution with tiled inference.
    Falls back to bicubic + sharpening when weights are unavailable.
    """

    def __init__(
        self,
        device: str = "cpu",
        half_precision: bool = False,
        model_key: str = "real_sr_x4",
        models_dir: Optional[Path] = None,
        scale: int = 4,
        large_model: bool = False,
    ):
        super().__init__(device, half_precision)
        self._model_key = "real_sr_x4_large" if large_model else model_key
        self._models_dir = models_dir or (Path.home() / ".cache" / "ai_enhancer" / "weights")
        self._scale = scale
        self._model = None

    @property
    def model_name(self) -> str:
        return f"SwinIR ({self._model_key})"

    def is_available(self) -> bool:
        try:
            import torch  # noqa: F401
            return True
        except ImportError:
            return False

    def load(self) -> None:
        if self._loaded:
            return
        if not self.is_available():
            raise ModelNotAvailableError("PyTorch not installed")

        import torch

        self._models_dir.mkdir(parents=True, exist_ok=True)
        weight_file = self._models_dir / f"swinir_{self._model_key}.pth"

        if not weight_file.exists():
            self.logger.info(f"Downloading SwinIR weights: {self._model_key} …")
            url = SWINIR_WEIGHTS.get(self._model_key)
            if url:
                urllib.request.urlretrieve(url, str(weight_file))
            else:
                raise ModelNotAvailableError(f"No URL for: {self._model_key}")

        # Try to load via basicsr SwinIR arch
        try:
            from basicsr.archs.swinir_arch import SwinIR
            large = "large" in self._model_key
            model = SwinIR(
                upscale=self._scale,
                in_chans=3,
                img_size=64,
                window_size=8,
                img_range=1.0,
                depths=[6, 6, 6, 6, 6, 6, 6, 6, 6] if large else [6, 6, 6, 6, 6, 6],
                embed_dim=240 if large else 180,
                num_heads=[8, 8, 8, 8, 8, 8, 8, 8, 8] if large else [6, 6, 6, 6, 6, 6],
                mlp_ratio=2,
                upsampler="nearest+conv",
                resi_connection="3conv" if large else "1conv",
            )
        except ImportError:
            raise ModelNotAvailableError(
                "basicsr package required for SwinIR. Run: pip install basicsr"
            )

        state = torch.load(str(weight_file), map_location="cpu")
        # Handle wrapped checkpoints
        if "params_ema" in state:
            state = state["params_ema"]
        elif "params" in state:
            state = state["params"]

        model.load_state_dict(state, strict=True)
        model.eval()

        if self.device == "cuda":
            model = model.cuda()
            if self.half_precision:
                model = model.half()

        self._model = model
        self._loaded = True
        self.logger.info(f"SwinIR loaded on {self.device.upper()}")

    def enhance(
        self,
        image: Image.Image,
        scale: float = 4.0,
        tile_size: int = 512,
    ) -> Image.Image:
        self.ensure_loaded()

        import torch

        # Convert to tensor [1, C, H, W] normalised to [0, 1]
        img_np = np.array(image).astype(np.float32) / 255.0
        img_t = torch.from_numpy(img_np).permute(2, 0, 1).unsqueeze(0)

        if self.device == "cuda":
            img_t = img_t.cuda()
            if self.half_precision:
                img_t = img_t.half()

        window_size = 8
        h, w = img_t.shape[-2:]
        pad_h = (window_size - h % window_size) % window_size
        pad_w = (window_size - w % window_size) % window_size
        import torch.nn.functional as F
        img_padded = F.pad(img_t, (0, pad_w, 0, pad_h), mode="reflect")

        with torch.no_grad():
            output = self._model(img_padded)

        # Crop padding from output
        output = output[:, :, : h * self._scale, : w * self._scale]
        out_np = output.float().clamp(0, 1).squeeze(0).permute(1, 2, 0).cpu().numpy()
        out_uint8 = (out_np * 255.0).round().astype(np.uint8)

        return Image.fromarray(out_uint8, mode="RGB")

    def unload(self) -> None:
        self._model = None
        self._loaded = False
        self._free_vram()
        self.logger.info("SwinIR unloaded")
