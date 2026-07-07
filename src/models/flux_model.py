"""
Flux Fill model wrapper for inpainting-based texture generation.
Flux is a state-of-the-art diffusion model by Black Forest Labs.

Requirements:
  - pip install diffusers transformers accelerate
  - ~12 GB VRAM recommended for Flux.1-Fill-dev
"""
import logging
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

from .base_model import BaseModel, ModelNotAvailableError

logger = logging.getLogger(__name__)

FLUX_FILL_MODEL_ID = "black-forest-labs/FLUX.1-Fill-dev"


class FluxFillModel(BaseModel):
    """
    Flux Fill for region-based texture reconstruction.
    Creates a full mask to regenerate the entire image with enhanced texture.
    """

    def __init__(
        self,
        device: str = "cpu",
        half_precision: bool = True,
        num_inference_steps: int = 28,
        guidance_scale: float = 30.0,
        prompt: str = (
            "ultra high resolution photograph, highly detailed textures, "
            "photorealistic, sharp focus, 8k"
        ),
    ):
        super().__init__(device, half_precision)
        self._steps = num_inference_steps
        self._guidance = guidance_scale
        self._prompt = prompt
        self._pipe = None

    @property
    def model_name(self) -> str:
        return "Flux Fill"

    def is_available(self) -> bool:
        try:
            import diffusers
            from packaging import version
            if version.parse(diffusers.__version__) >= version.parse("0.30.0"):
                return True
        except Exception:
            pass
        try:
            from diffusers import FluxFillPipeline  # noqa: F401
            return True
        except ImportError:
            return False

    def load(self) -> None:
        if self._loaded:
            return
        if not self.is_available():
            raise ModelNotAvailableError(
                "FluxFillPipeline not available.\n"
                "Run: pip install diffusers>=0.30 transformers accelerate\n"
                "Note: Requires ~12 GB VRAM and HuggingFace token for gated model."
            )

        import torch
        from diffusers import FluxFillPipeline

        dtype = torch.bfloat16 if self.half_precision else torch.float32

        self.logger.info("Loading Flux Fill model (large, may take several minutes) …")

        self._pipe = FluxFillPipeline.from_pretrained(
            FLUX_FILL_MODEL_ID,
            torch_dtype=dtype,
        )

        if self.device == "cuda":
            self._pipe.enable_model_cpu_offload()

        self._pipe.set_progress_bar_config(disable=True)
        self._loaded = True
        self.logger.info("Flux Fill loaded")

    def enhance(
        self,
        image: Image.Image,
        scale: float = 1.0,
        tile_size: int = 512,
    ) -> Image.Image:
        self.ensure_loaded()

        import torch

        # Full-image mask (all white = regenerate everything)
        mask = Image.new("RGB", image.size, (255, 255, 255))

        result = self._pipe(
            prompt=self._prompt,
            image=image,
            mask_image=mask,
            num_inference_steps=self._steps,
            guidance_scale=self._guidance,
            generator=torch.Generator(device=self.device).manual_seed(42),
        ).images[0]

        return result

    def unload(self) -> None:
        self._pipe = None
        self._loaded = False
        self._free_vram()
        self.logger.info("Flux Fill unloaded")
