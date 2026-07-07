"""
Stable Diffusion XL Image-to-Image model wrapper.
Uses the diffusers library for high-quality texture reconstruction.

Requirements:
  - pip install diffusers transformers accelerate xformers
  - ~8 GB VRAM recommended (fp16 mode)
  - Model auto-downloaded from HuggingFace on first use
"""
import logging
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

from .base_model import BaseModel, ModelNotAvailableError

logger = logging.getLogger(__name__)

SDXL_MODEL_ID = "stabilityai/stable-diffusion-xl-base-1.0"
SDXL_REFINER_ID = "stabilityai/stable-diffusion-xl-refiner-1.0"


class SDXLImg2ImgModel(BaseModel):
    """
    SDXL Image-to-Image for texture reconstruction and detail generation.
    Uses a very low strength (0.25–0.40) to preserve composition while
    adding realistic textures.
    """

    def __init__(
        self,
        device: str = "cpu",
        half_precision: bool = True,
        models_dir: Optional[Path] = None,
        strength: float = 0.30,
        guidance_scale: float = 7.5,
        num_inference_steps: int = 30,
        prompt: str = (
            "high resolution, sharp details, natural textures, photorealistic, "
            "8k uhd, highly detailed, professional photography"
        ),
        negative_prompt: str = (
            "blurry, low quality, artifacts, noise, oversaturated, "
            "overexposed, watermark, text"
        ),
    ):
        super().__init__(device, half_precision)
        self._models_dir = models_dir
        self._strength = strength
        self._guidance_scale = guidance_scale
        self._steps = num_inference_steps
        self._prompt = prompt
        self._negative_prompt = negative_prompt
        self._pipe = None

    @property
    def model_name(self) -> str:
        return "Stable Diffusion XL Img2Img"

    def is_available(self) -> bool:
        try:
            import diffusers  # noqa: F401
            import transformers  # noqa: F401
            return True
        except ImportError:
            return False

    def load(self) -> None:
        if self._loaded:
            return
        if not self.is_available():
            raise ModelNotAvailableError(
                "diffusers package not installed.\n"
                "Run: pip install diffusers transformers accelerate"
            )

        import torch
        from diffusers import StableDiffusionXLImg2ImgPipeline

        dtype = torch.float16 if self.half_precision else torch.float32

        self.logger.info(f"Loading SDXL (this may take a while on first run) …")
        self._pipe = StableDiffusionXLImg2ImgPipeline.from_pretrained(
            SDXL_MODEL_ID,
            torch_dtype=dtype,
            use_safetensors=True,
            variant="fp16" if self.half_precision else None,
        )

        if self.device == "cuda":
            self._pipe = self._pipe.to("cuda")
            try:
                self._pipe.enable_xformers_memory_efficient_attention()
            except Exception:
                pass

        self._pipe.set_progress_bar_config(disable=True)
        self._loaded = True
        self.logger.info("SDXL Img2Img loaded")

    def enhance(
        self,
        image: Image.Image,
        scale: float = 1.0,
        tile_size: int = 512,
    ) -> Image.Image:
        self.ensure_loaded()

        import torch

        result = self._pipe(
            prompt=self._prompt,
            negative_prompt=self._negative_prompt,
            image=image,
            strength=self._strength,
            guidance_scale=self._guidance_scale,
            num_inference_steps=self._steps,
            generator=torch.Generator(device=self.device).manual_seed(42),
        ).images[0]

        return result

    def unload(self) -> None:
        self._pipe = None
        self._loaded = False
        self._free_vram()
        self.logger.info("SDXL Img2Img unloaded")
