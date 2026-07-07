"""
Abstract base class for all AI enhancement models.
All model implementations must inherit from BaseModel.
"""
import logging
from abc import ABC, abstractmethod
from pathlib import Path

import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


class ModelNotAvailableError(Exception):
    """Raised when a model cannot be loaded (missing weights or dependencies)."""


class BaseModel(ABC):
    """
    Abstract base for AI enhancement models.

    Subclasses must implement:
        - model_name (property)
        - is_available() → bool
        - load()
        - enhance(image, scale) → Image
        - unload()
    """

    def __init__(self, device: str = "cpu", half_precision: bool = False):
        self.device = device
        self.half_precision = half_precision and device == "cuda"
        self._loaded = False
        self.logger = logging.getLogger(self.__class__.__name__)

    # ------------------------------------------------------------------ #
    # Abstract interface
    # ------------------------------------------------------------------ #

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Human-readable model identifier."""

    @abstractmethod
    def is_available(self) -> bool:
        """
        Returns True if all required packages and weights are available.
        Must NOT download anything — only check existence.
        """

    @abstractmethod
    def load(self) -> None:
        """
        Load model weights into memory.
        Should set self._loaded = True on success.
        Downloads weights if needed.
        """

    @abstractmethod
    def enhance(
        self,
        image: Image.Image,
        scale: float = 4.0,
        tile_size: int = 512,
    ) -> Image.Image:
        """
        Run AI enhancement on the input image.

        Args:
            image:     Input PIL Image (RGB).
            scale:     Upscale factor (e.g. 2.0, 4.0).
            tile_size: Tile size for processing (reduces VRAM).

        Returns:
            Enhanced PIL Image (RGB).
        """

    @abstractmethod
    def unload(self) -> None:
        """
        Release model from GPU/CPU memory.
        Should set self._loaded = False.
        """

    # ------------------------------------------------------------------ #
    # Helpers
    # ------------------------------------------------------------------ #

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    def ensure_loaded(self) -> None:
        """Load the model if it is not already loaded."""
        if not self._loaded:
            self.logger.info(f"Loading model: {self.model_name}")
            self.load()

    def _free_vram(self) -> None:
        """Release CUDA cache."""
        if self.device == "cuda":
            try:
                import torch
                torch.cuda.empty_cache()
            except Exception:
                pass

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}("
            f"device={self.device!r}, loaded={self._loaded})"
        )
