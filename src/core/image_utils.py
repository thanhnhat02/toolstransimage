"""
Image I/O utilities shared across the pipeline.
Handles reading, writing, format conversion, and resolution calculation.
"""
import logging
from pathlib import Path
from typing import Optional, Tuple

import cv2
import numpy as np
from PIL import Image, ImageCms

logger = logging.getLogger(__name__)

SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".webp", ".bmp", ".tiff", ".tif"}


def is_supported(path: Path) -> bool:
    """Returns True if the file extension is supported."""
    return path.suffix.lower() in SUPPORTED_FORMATS


def scan_folder(folder: Path, recursive: bool = False) -> list[Path]:
    """
    Scans a folder for supported image files.

    Args:
        folder:    Directory to scan.
        recursive: If True, also scans sub-directories.

    Returns:
        Sorted list of image Paths.
    """
    pattern = "**/*" if recursive else "*"
    images = [
        p
        for p in folder.glob(pattern)
        if p.is_file() and is_supported(p)
    ]
    images.sort(key=lambda p: p.name.lower())
    logger.info(f"Found {len(images)} image(s) in '{folder}'")
    return images


def load_image_cv2(path: Path) -> np.ndarray:
    """
    Load an image as an OpenCV BGR numpy array.
    Handles EXIF orientation automatically.
    """
    img = cv2.imread(str(path), cv2.IMREAD_COLOR)
    if img is None:
        raise FileNotFoundError(f"Cannot load image: {path}")
    return img


def load_image_pil(path: Path) -> Image.Image:
    """
    Load image as a Pillow Image.
    Converts to RGB and applies EXIF rotation.
    """
    img = Image.open(path)
    # Apply EXIF rotation
    try:
        from PIL import ImageOps
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass
    return img.convert("RGB")


def pil_to_cv2(img: Image.Image) -> np.ndarray:
    """Convert PIL RGB Image → OpenCV BGR ndarray."""
    return cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)


def cv2_to_pil(arr: np.ndarray) -> Image.Image:
    """Convert OpenCV BGR ndarray → PIL RGB Image."""
    return Image.fromarray(cv2.cvtColor(arr, cv2.COLOR_BGR2RGB))


def calculate_output_size(
    width: int, height: int, target: str
) -> Tuple[int, int, float]:
    """
    Calculate the output resolution and upscale factor.

    Args:
        width, height: Original image dimensions.
        target:        One of '2K', '4K', '8K', '2x', '4x', 'original'.

    Returns:
        (new_width, new_height, scale_factor)
    """
    TARGETS = {
        "2K":   (2560, 1440),
        "4K":   (3840, 2160),
        "8K":   (7680, 4320),
        "2x":   None,
        "4x":   None,
        "original": None,
    }

    if target == "original":
        return width, height, 1.0

    if target == "2x":
        return width * 2, height * 2, 2.0

    if target == "4x":
        return width * 4, height * 4, 4.0

    if target in ("2K", "4K", "8K"):
        tw, th = TARGETS[target]
        scale = min(tw / width, th / height)
        if scale <= 1.0:
            # Image already meets or exceeds target — still apply AI
            scale = 1.0
        new_w = int(width * scale)
        new_h = int(height * scale)
        return new_w, new_h, scale

    # Fallback
    return width * 4, height * 4, 4.0


def save_image(
    img: Image.Image,
    output_path: Path,
    fmt: str = "PNG",
    jpeg_quality: int = 95,
) -> None:
    """
    Save a PIL image to disk.

    Args:
        img:          PIL Image (RGB).
        output_path:  Destination file path.
        fmt:          'PNG', 'JPEG', or 'WEBP'.
        jpeg_quality: Quality for lossy formats (0-100).
    """
    output_path.parent.mkdir(parents=True, exist_ok=True)
    fmt_upper = fmt.upper()

    if fmt_upper == "PNG":
        img.save(str(output_path), format="PNG", optimize=False, compress_level=1)
    elif fmt_upper in ("JPEG", "JPG"):
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.save(str(output_path), format="JPEG", quality=jpeg_quality, subsampling=0)
    elif fmt_upper == "WEBP":
        img.save(str(output_path), format="WEBP", quality=100, method=6)
    else:
        img.save(str(output_path), format="PNG")

    logger.debug(f"Saved → {output_path} ({fmt_upper})")


def get_output_path(
    input_path: Path,
    output_dir: Path,
    export_format: str,
) -> Path:
    """
    Compute output path preserving the original filename.
    Only the extension may change (if format changes from jpg to png etc).

    Rules:
    - Keep original stem (no suffixes added).
    - Save into output_dir only.
    - Change extension to match export_format.
    """
    stem = input_path.stem  # e.g. "photo001" — no modification
    ext_map = {
        "PNG": ".png",
        "JPEG": ".jpg",
        "JPG": ".jpg",
        "WEBP": ".webp",
    }
    new_ext = ext_map.get(export_format.upper(), ".png")
    return output_dir / f"{stem}{new_ext}"
