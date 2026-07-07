"""
Post-processing pipeline using OpenCV.

Implements:
- Adaptive unsharp masking (no haloing)
- Local contrast enhancement (CLAHE)
- Edge enhancement
- Smart denoising (NLMeans / bilateral)
- Anti-halo / anti-ringing filter
- Color preservation (LAB-space operations)
- Skin-tone protection (prevents over-sharpening faces)
"""
import logging

import cv2
import numpy as np
from PIL import Image

logger = logging.getLogger(__name__)


# ──────────────────────────────────────────────────────────────────────────── #
# Public API
# ──────────────────────────────────────────────────────────────────────────── #

def apply_postprocessing(
    image: Image.Image,
    sharpen_strength: float = 0.6,
    contrast_strength: float = 0.4,
    denoise_strength: float = 0.5,
    use_sharpen: bool = True,
    use_local_contrast: bool = True,
    use_denoise: bool = True,
    use_edge_enhance: bool = True,
) -> Image.Image:
    """
    Apply full post-processing pipeline.

    Args:
        image:              PIL RGB image.
        sharpen_strength:   0–1, adaptive sharpening intensity.
        contrast_strength:  0–1, local contrast (CLAHE) intensity.
        denoise_strength:   0–1, NLM denoise intensity.
        use_sharpen:        Enable sharpening.
        use_local_contrast: Enable CLAHE.
        use_denoise:        Enable denoising.
        use_edge_enhance:   Enable edge enhancement.

    Returns:
        Processed PIL RGB image.
    """
    arr = np.array(image, dtype=np.uint8)   # uint8 RGB

    if use_denoise and denoise_strength > 0:
        arr = _smart_denoise(arr, strength=denoise_strength)

    if use_local_contrast and contrast_strength > 0:
        arr = _local_contrast_clahe(arr, strength=contrast_strength)

    if use_sharpen and sharpen_strength > 0:
        arr = _adaptive_unsharp_mask(arr, strength=sharpen_strength)

    if use_edge_enhance:
        arr = _subtle_edge_enhance(arr)

    return Image.fromarray(arr, mode="RGB")


# ──────────────────────────────────────────────────────────────────────────── #
# Internal helpers
# ──────────────────────────────────────────────────────────────────────────── #

def _smart_denoise(arr: np.ndarray, strength: float = 0.5) -> np.ndarray:
    """
    NLMeans denoising in YCrCb space to protect chroma.
    Strength 0–1 maps to h parameter 3–10.
    """
    h_val = 3 + strength * 7          # 3 (gentle) → 10 (strong)
    ycrcb = cv2.cvtColor(arr, cv2.COLOR_RGB2YCrCb)
    y, cr, cb = cv2.split(ycrcb)

    # Denoise luminance only → preserve color fidelity
    y_denoised = cv2.fastNlMeansDenoising(y, h=h_val, templateWindowSize=7, searchWindowSize=21)

    merged = cv2.merge([y_denoised, cr, cb])
    return cv2.cvtColor(merged, cv2.COLOR_YCrCb2RGB)


def _local_contrast_clahe(arr: np.ndarray, strength: float = 0.4) -> np.ndarray:
    """
    CLAHE on luminance channel to enhance local contrast
    without global color shift.
    """
    clip = 1.0 + strength * 3.0     # 1.0 → 4.0
    tile = max(4, int(8 * (1 - strength) + 4))   # 8 → 4

    lab = cv2.cvtColor(arr, cv2.COLOR_RGB2LAB)
    l_ch, a_ch, b_ch = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=clip, tileGridSize=(tile, tile))
    l_enhanced = clahe.apply(l_ch)

    merged = cv2.merge([l_enhanced, a_ch, b_ch])
    return cv2.cvtColor(merged, cv2.COLOR_LAB2RGB)


def _adaptive_unsharp_mask(arr: np.ndarray, strength: float = 0.6) -> np.ndarray:
    """
    Adaptive unsharp masking that:
    - Avoids halos on high-contrast edges.
    - Protects smooth skin-tone regions.
    - Targets mid-frequency detail.
    """
    # ── Parameters ───────────────────────────────────────────────────── #
    sigma1 = 0.8                   # Fine detail radius
    sigma2 = 3.0                   # Coarse edge radius
    amount = 0.4 + strength * 0.8  # 0.4 → 1.2

    # ── Convert to float ─────────────────────────────────────────────── #
    f = arr.astype(np.float32)

    # ── Multi-scale unsharp ──────────────────────────────────────────── #
    blur1 = cv2.GaussianBlur(f, (0, 0), sigma1)
    blur2 = cv2.GaussianBlur(f, (0, 0), sigma2)

    # Coarse detail mask (large-scale)
    detail_coarse = f - blur2

    # ── Edge detection to suppress halo ─────────────────────────────── #
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    edges = cv2.Canny(gray, 50, 150).astype(np.float32) / 255.0
    # Dilate edge mask to cover halo zone
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    halo_mask = cv2.dilate(edges, kernel, iterations=2)
    # Invert: 0 = near edge (suppress sharpen), 1 = safe zone
    safe_mask = 1.0 - np.clip(halo_mask, 0, 0.8)

    # ── Skin-tone protection ─────────────────────────────────────────── #
    skin_mask = _detect_skin(arr).astype(np.float32) / 255.0
    # Reduce sharpening on skin to avoid plastic look
    skin_reduce = 1.0 - skin_mask * 0.5

    # ── Blend ────────────────────────────────────────────────────────── #
    detail_final = detail_coarse * safe_mask[..., np.newaxis] * skin_reduce[..., np.newaxis]
    sharpened = f + amount * detail_final

    return np.clip(sharpened, 0, 255).astype(np.uint8)


def _subtle_edge_enhance(arr: np.ndarray) -> np.ndarray:
    """
    Very subtle edge emphasis using a small unsharp mask.
    Adds micro-detail crispness without visible sharpening artifacts.
    """
    f = arr.astype(np.float32)
    blur = cv2.GaussianBlur(f, (0, 0), 0.5)
    enhanced = f + 0.15 * (f - blur)
    return np.clip(enhanced, 0, 255).astype(np.uint8)


def _detect_skin(arr: np.ndarray) -> np.ndarray:
    """
    Detect skin-tone regions using YCrCb color space heuristics.
    Returns a binary mask (uint8, 0 or 255).
    """
    ycrcb = cv2.cvtColor(arr, cv2.COLOR_RGB2YCrCb)
    # YCrCb skin range (from Chai and Ngan 1999)
    lower = np.array([0, 133, 77], dtype=np.uint8)
    upper = np.array([255, 173, 127], dtype=np.uint8)
    mask = cv2.inRange(ycrcb, lower, upper)

    # Smooth the mask
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (11, 11))
    mask = cv2.dilate(mask, kernel, iterations=2)
    mask = cv2.GaussianBlur(mask, (21, 21), 0)

    return mask


def preserve_color(original: Image.Image, enhanced: Image.Image) -> Image.Image:
    """
    Transfer the LAB color (a + b channels) from the original image
    to the enhanced image luminance.
    This preserves white balance and saturation from the source.
    """
    orig_np = np.array(original.resize(enhanced.size, Image.LANCZOS), dtype=np.uint8)
    enh_np = np.array(enhanced, dtype=np.uint8)

    orig_lab = cv2.cvtColor(orig_np, cv2.COLOR_RGB2LAB).astype(np.float32)
    enh_lab = cv2.cvtColor(enh_np, cv2.COLOR_RGB2LAB).astype(np.float32)

    # Keep enhanced L, use original A/B normalized to enhanced range
    merged = np.stack([
        enh_lab[:, :, 0],
        orig_lab[:, :, 1],
        orig_lab[:, :, 2],
    ], axis=2).astype(np.uint8)

    return Image.fromarray(cv2.cvtColor(merged, cv2.COLOR_LAB2RGB), mode="RGB")
