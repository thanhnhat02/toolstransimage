"""
ControlNet Tile model wrapper.
Uses ControlNet with a Tile conditioning image to add fine-grained
detail while preserving the overall structure of the input image.

Requirements:
  - pip install diffusers controlnet-aux transformers accelerate
  - ~10 GB VRAM recommended
"""
import logging
from pathlib import Path
from typing import Optional

import numpy as np
from PIL import Image

from .base_model import BaseModel, ModelNotAvailableError

logger = logging.getLogger(__name__)

CONTROLNET_TILE_ID = "lllyasviel/control_v11f1e_sd15_tile"
SD15_MODEL_ID = "runwayml/stable-diffusion-v1-5"


class ControlNetTileModel(BaseModel):
    """
    ControlNet Tile for ultra-detail enhancement.
    Conditions on a downsampled + upsampled tile to force the model
    to regenerate local texture details.
    """

    def __init__(
        self,
        device: str = "cpu",
        half_precision: bool = True,
        strength: float = 0.5,
        guidance_scale: float = 7.5,
        num_inference_steps: int = 25,
        prompt: str = (
            "masterpiece, best quality, ultra detailed, sharp focus, "
            "realistic, high resolution texture, natural lighting"
        ),
        negative_prompt: str = (
            "blurry, low quality, noise, artifacts, watermark, "
            "text, signature, overexposed"
        ),
    ):
        super().__init__(device, half_precision)
        self._strength = strength
        self._guidance_scale = guidance_scale
        self._steps = num_inference_steps
        self._prompt = prompt
        self._negative_prompt = negative_prompt
        self._pipe = None

    @property
    def model_name(self) -> str:
        return "ControlNet Tile"

    def is_available(self) -> bool:
        try:
            import diffusers  # noqa: F401
            import controlnet_aux  # noqa: F401
            return True
        except ImportError:
            return False

    def load(self) -> None:
        if self._loaded:
            return
        if not self.is_available():
            raise ModelNotAvailableError(
                "diffusers or controlnet-aux not installed.\n"
                "Run: pip install diffusers controlnet-aux"
            )

        import torch
        from diffusers import (
            ControlNetModel,
            StableDiffusionControlNetImg2ImgPipeline,
            UniPCMultistepScheduler,
        )

        dtype = torch.float16 if self.half_precision else torch.float32

        self.logger.info("Loading ControlNet Tile (first run may take time) …")

        controlnet = ControlNetModel.from_pretrained(
            CONTROLNET_TILE_ID, torch_dtype=dtype
        )
        self._pipe = StableDiffusionControlNetImg2ImgPipeline.from_pretrained(
            SD15_MODEL_ID,
            controlnet=controlnet,
            torch_dtype=dtype,
            safety_checker=None,
        )
        self._pipe.scheduler = UniPCMultistepScheduler.from_config(
            self._pipe.scheduler.config
        )

        if self.device == "cuda":
            self._pipe = self._pipe.to("cuda")
            try:
                self._pipe.enable_xformers_memory_efficient_attention()
            except Exception:
                pass

        self._pipe.set_progress_bar_config(disable=True)
        self._loaded = True
        self.logger.info("ControlNet Tile loaded")

    def enhance(
        self,
        image: Image.Image,
        scale: float = 1.0,
        tile_size: int = 512,
    ) -> Image.Image:
        self.ensure_loaded()

        import torch

        # Create tile conditioning image (blur → upscale → use as control)
        w, h = image.size
        control = image.resize((w // 2, h // 2), Image.LANCZOS)
        control = control.resize((w, h), Image.LANCZOS)

        result = self._pipe(
            prompt=self._prompt,
            negative_prompt=self._negative_prompt,
            image=image,
            control_image=control,
            strength=self._strength,
            guidance_scale=self._guidance_scale,
            num_inference_steps=self._steps,
            controlnet_conditioning_scale=1.0,
            generator=torch.Generator(device=self.device).manual_seed(42),
        ).images[0]

        return result

    def unload(self) -> None:
        self._pipe = None
        self._loaded = False
        self._free_vram()
        self.logger.info("ControlNet Tile unloaded")
