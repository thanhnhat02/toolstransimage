"""
Main image processing pipeline.
Orchestrates model selection, enhancement, post-processing, and export.
"""
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional

from PIL import Image

from src.core.gpu_detector import get_device, get_half_precision_support
from src.core.image_utils import (
    calculate_output_size,
    get_output_path,
    load_image_pil,
    save_image,
)
from src.models.face_restore_model import FaceRestoreModel
from src.pipeline.postprocessing import apply_postprocessing, preserve_color

logger = logging.getLogger(__name__)


@dataclass
class ProcessingConfig:
    """All parameters required for processing a single image."""
    ai_mode: str = "real_esrgan"          # Model selection key
    upscale_target: str = "4K"            # '2K', '4K', '8K', '2x', '4x', 'original'
    export_format: str = "PNG"            # 'PNG', 'JPEG', 'WEBP'
    use_gpu: bool = True
    use_face_restore: bool = True
    use_denoise: bool = True
    use_sharpen: bool = True
    use_local_contrast: bool = True
    use_edge_enhance: bool = True
    denoise_strength: float = 0.5
    sharpen_strength: float = 0.6
    contrast_strength: float = 0.4
    half_precision: bool = True
    tile_size: int = 512
    jpeg_quality: int = 95
    models_dir: Optional[Path] = None
    output_dir: Optional[Path] = None


@dataclass
class ProcessingResult:
    """Result of processing a single image."""
    input_path: Path
    output_path: Optional[Path] = None
    success: bool = False
    error: Optional[str] = None
    elapsed_seconds: float = 0.0
    original_size: tuple = (0, 0)
    output_size: tuple = (0, 0)


class ImageProcessor:
    """
    Core processing engine. Loads models on demand and processes images
    according to the selected pipeline mode.
    """

    AI_MODES = {
        "real_esrgan":   "Real-ESRGAN",
        "swinir":        "SwinIR",
        "supir":         "SUPIR",
        "sdxl":          "Stable Diffusion XL Img2Img",
        "controlnet":    "ControlNet Tile",
        "flux_fill":     "Flux Fill",
        "hybrid":        "Hybrid (Recommended)",
    }

    def __init__(self, config: ProcessingConfig):
        self.config = config
        self._device = get_device(prefer_gpu=config.use_gpu)
        self._half = get_half_precision_support(self._device) and config.half_precision
        self._models_dir = config.models_dir or (
            Path.home() / ".cache" / "ai_enhancer" / "weights"
        )
        self._upscale_model = None
        self._face_model: Optional[FaceRestoreModel] = None
        self._models_loaded = False

    # ------------------------------------------------------------------ #
    # Public API
    # ------------------------------------------------------------------ #

    def load_models(self, progress_cb: Optional[Callable[[str], None]] = None) -> None:
        """Pre-load all models required for the selected mode."""
        def _cb(msg):
            if progress_cb:
                progress_cb(msg)
            logger.info(msg)

        _cb(f"Device: {self._device.upper()}")
        _cb(f"Mode: {self.AI_MODES.get(self.config.ai_mode, self.config.ai_mode)}")

        # ── Upscale model ────────────────────────────────────────────── #
        _cb("Loading upscale model …")
        self._upscale_model = self._build_upscale_model()
        try:
            self._upscale_model.load()
            _cb(f"✓ {self._upscale_model.model_name} ready")
        except Exception as e:
            logger.warning(f"Primary model failed ({e}), trying fallback …")
            self._upscale_model = self._build_fallback_model()
            self._upscale_model.load()
            _cb(f"✓ Fallback: {self._upscale_model.model_name} ready")

        # ── Face restoration ─────────────────────────────────────────── #
        if self.config.use_face_restore:
            _cb("Loading face restore model …")
            try:
                self._face_model = FaceRestoreModel(
                    device=self._device,
                    half_precision=self._half,
                    models_dir=self._models_dir,
                )
                self._face_model.load()
                _cb("✓ Face restore ready")
            except Exception as e:
                logger.warning(f"Face restore unavailable: {e}")
                self._face_model = None

        self._models_loaded = True
        _cb("All models loaded — ready to process")

    def unload_models(self) -> None:
        """Free GPU/CPU memory by unloading all models."""
        if self._upscale_model:
            self._upscale_model.unload()
        if self._face_model:
            self._face_model.unload()
        self._models_loaded = False

    def process_image(
        self,
        input_path: Path,
        output_dir: Path,
        progress_cb: Optional[Callable[[str], None]] = None,
    ) -> ProcessingResult:
        """
        Process a single image through the complete pipeline.

        Args:
            input_path:  Path to source image.
            output_dir:  Directory to save the result.
            progress_cb: Called with status messages during processing.

        Returns:
            ProcessingResult with success status and timing.
        """
        start = time.perf_counter()
        result = ProcessingResult(input_path=input_path)

        def _cb(msg):
            if progress_cb:
                progress_cb(msg)
            logger.debug(msg)

        try:
            if not self._models_loaded:
                self.load_models(progress_cb=progress_cb)

            # ── Load image ─────────────────────────────────────────── #
            _cb(f"Loading: {input_path.name}")
            original = load_image_pil(input_path)
            result.original_size = original.size
            ow, oh = original.size

            # ── Compute target scale ───────────────────────────────── #
            new_w, new_h, scale_factor = calculate_output_size(
                ow, oh, self.config.upscale_target
            )
            # Real-ESRGAN native scales: 2x or 4x
            esrgan_scale = 4.0 if scale_factor > 2.0 else 2.0

            # ── AI Upscale ─────────────────────────────────────────── #
            _cb(f"AI upscaling ({self._upscale_model.model_name}) …")
            enhanced = self._upscale_model.enhance(
                original,
                scale=esrgan_scale,
                tile_size=self.config.tile_size,
            )

            # ── Resize to exact target resolution ──────────────────── #
            if enhanced.size != (new_w, new_h):
                enhanced = enhanced.resize((new_w, new_h), Image.LANCZOS)

            # ── Hybrid: extra AI pass ──────────────────────────────── #
            if self.config.ai_mode == "hybrid":
                enhanced = self._apply_hybrid_extras(enhanced, _cb)

            # ── Face restoration ───────────────────────────────────── #
            if self.config.use_face_restore and self._face_model:
                _cb("Restoring faces …")
                enhanced = self._face_model.enhance(enhanced)

            # ── Post-processing ────────────────────────────────────── #
            _cb("Applying post-processing …")
            enhanced = apply_postprocessing(
                enhanced,
                sharpen_strength=self.config.sharpen_strength,
                contrast_strength=self.config.contrast_strength,
                denoise_strength=self.config.denoise_strength,
                use_sharpen=self.config.use_sharpen,
                use_local_contrast=self.config.use_local_contrast,
                use_denoise=self.config.use_denoise,
                use_edge_enhance=self.config.use_edge_enhance,
            )

            # ── Color preservation ─────────────────────────────────── #
            _cb("Preserving colors …")
            enhanced = preserve_color(original, enhanced)

            # ── Export ─────────────────────────────────────────────── #
            output_path = get_output_path(
                input_path, output_dir, self.config.export_format
            )
            _cb(f"Saving → {output_path.name}")
            save_image(
                enhanced,
                output_path,
                fmt=self.config.export_format,
                jpeg_quality=self.config.jpeg_quality,
            )

            result.output_path = output_path
            result.output_size = enhanced.size
            result.success = True

        except Exception as e:
            logger.exception(f"Processing failed for {input_path.name}: {e}")
            result.error = str(e)

        result.elapsed_seconds = time.perf_counter() - start
        return result

    # ------------------------------------------------------------------ #
    # Private helpers
    # ------------------------------------------------------------------ #

    def _build_upscale_model(self):
        mode = self.config.ai_mode
        kwargs = {
            "device": self._device,
            "half_precision": self._half,
            "models_dir": self._models_dir,
        }

        if mode in ("real_esrgan", "hybrid"):
            from src.models.real_esrgan_model import RealESRGANModel
            return RealESRGANModel(**kwargs)
        elif mode == "swinir":
            from src.models.swinir_model import SwinIRModel
            return SwinIRModel(**kwargs)
        elif mode == "supir":
            from src.models.supir_model import SUPIRModel
            return SUPIRModel(**{k: v for k, v in kwargs.items() if k != "models_dir"})
        elif mode == "sdxl":
            from src.models.sdxl_model import SDXLImg2ImgModel
            return SDXLImg2ImgModel(**{k: v for k, v in kwargs.items() if k != "models_dir"})
        elif mode == "controlnet":
            from src.models.controlnet_model import ControlNetTileModel
            return ControlNetTileModel(**{k: v for k, v in kwargs.items() if k != "models_dir"})
        elif mode == "flux_fill":
            from src.models.flux_model import FluxFillModel
            return FluxFillModel(**{k: v for k, v in kwargs.items() if k != "models_dir"})
        else:
            from src.models.real_esrgan_model import RealESRGANModel
            return RealESRGANModel(**kwargs)

    def _build_fallback_model(self):
        """Try SwinIR then Real-ESRGAN as fallbacks."""
        logger.info("Using Real-ESRGAN as fallback upscaler")
        from src.models.real_esrgan_model import RealESRGANModel
        return RealESRGANModel(
            device=self._device,
            half_precision=self._half,
            models_dir=self._models_dir,
        )

    def _apply_hybrid_extras(
        self,
        image: Image.Image,
        cb: Callable[[str], None],
    ) -> Image.Image:
        """
        In Hybrid mode, apply an optional SDXL texture pass
        if VRAM allows, otherwise skip gracefully.
        """
        try:
            from src.models.sdxl_model import SDXLImg2ImgModel
            sdxl = SDXLImg2ImgModel(
                device=self._device,
                half_precision=self._half,
                strength=0.25,  # Very gentle — preserve structure
            )
            if sdxl.is_available():
                cb("Hybrid: adding SDXL texture …")
                sdxl.load()
                image = sdxl.enhance(image)
                sdxl.unload()
        except Exception as e:
            logger.debug(f"Hybrid SDXL pass skipped: {e}")
        return image
