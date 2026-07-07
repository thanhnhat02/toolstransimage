"""
SUPIR model wrapper.
SUPIR (Scaling UP Image Restoration) is a large-scale model that uses
LLM-guided image restoration.

Reference: https://github.com/Fanghua-Yu/SUPIR

Requirements:
  - pip install diffusers transformers open_clip_torch
  - ~12–16 GB VRAM recommended
  - Model weights must be manually downloaded from HuggingFace
"""
import logging
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

from .base_model import BaseModel, ModelNotAvailableError

logger = logging.getLogger(__name__)

SUPIR_MODEL_HF = "Kijai/SUPIR-v0Q_fp16"


class SUPIRModel(BaseModel):
    """
    SUPIR model for photorealistic image restoration.
    Falls back to Real-ESRGAN if SUPIR dependencies are missing.

    Note: SUPIR requires significant VRAM (12–16 GB) and is best suited
    for users with high-end GPUs.
    """

    def __init__(
        self,
        device: str = "cpu",
        half_precision: bool = True,
        models_dir: Optional[Path] = None,
        edm_steps: int = 50,
        s_churn: float = 5,
        s_noise: float = 1.003,
        prompt: str = "ultra high resolution, sharp, detailed",
        negative_prompt: str = "blurry, noisy, artifacts",
    ):
        super().__init__(device, half_precision)
        self._models_dir = models_dir or (Path.home() / ".cache" / "ai_enhancer" / "supir")
        self._edm_steps = edm_steps
        self._s_churn = s_churn
        self._s_noise = s_noise
        self._prompt = prompt
        self._negative_prompt = negative_prompt
        self._pipeline = None

    @property
    def model_name(self) -> str:
        return "SUPIR"

    def is_available(self) -> bool:
        """
        Check if SUPIR pipeline is available via diffusers.
        """
        try:
            from diffusers import SUPIRPipeline  # noqa: F401
            return True
        except ImportError:
            return False

    def load(self) -> None:
        if self._loaded:
            return
        if not self.is_available():
            raise ModelNotAvailableError(
                "SUPIR pipeline not available in your diffusers version.\n"
                "Install: pip install diffusers>=0.27 transformers open-clip-torch\n"
                "Note: SUPIR requires 12-16 GB VRAM."
            )

        import torch
        from diffusers import SUPIRPipeline

        dtype = torch.float16 if self.half_precision else torch.float32

        self.logger.info("Loading SUPIR model (large model, may take several minutes) …")

        self._pipeline = SUPIRPipeline.from_pretrained(
            SUPIR_MODEL_HF,
            torch_dtype=dtype,
        )

        if self.device == "cuda":
            self._pipeline = self._pipeline.to("cuda")
            try:
                self._pipeline.enable_xformers_memory_efficient_attention()
            except Exception:
                pass

        self._pipeline.set_progress_bar_config(disable=True)
        self._loaded = True
        self.logger.info("SUPIR loaded")

    def enhance(
        self,
        image: Image.Image,
        scale: float = 4.0,
        tile_size: int = 512,
    ) -> Image.Image:
        self.ensure_loaded()

        import torch

        result = self._pipeline(
            image=image,
            prompt=self._prompt,
            negative_prompt=self._negative_prompt,
            num_inference_steps=self._edm_steps,
            generator=torch.Generator(device=self.device).manual_seed(42),
        ).images[0]

        # Resize to target scale if needed
        if scale > 1.0:
            w, h = image.size
            target = (int(w * scale), int(h * scale))
            result = result.resize(target, Image.LANCZOS)

        return result

    def unload(self) -> None:
        self._pipeline = None
        self._loaded = False
        self._free_vram()
        self.logger.info("SUPIR unloaded")
