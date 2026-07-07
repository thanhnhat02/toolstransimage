"""
GPU / Device detection utility.
Automatically detects CUDA availability and returns the optimal device.
"""
import logging
from typing import Optional

logger = logging.getLogger(__name__)


def get_device(prefer_gpu: bool = True) -> str:
    """
    Returns the best available compute device string.

    Priority: CUDA → CPU

    Args:
        prefer_gpu: If False, forces CPU even when GPU is available.

    Returns:
        'cuda' | 'cpu'
    """
    if not prefer_gpu:
        logger.info("GPU disabled by user preference — using CPU")
        return "cpu"

    try:
        import torch
        if torch.cuda.is_available():
            device_name = torch.cuda.get_device_name(0)
            vram_gb = torch.cuda.get_device_properties(0).total_memory / (1024 ** 3)
            logger.info(f"CUDA GPU detected: {device_name} ({vram_gb:.1f} GB VRAM)")
            return "cuda"
        else:
            logger.info("No CUDA GPU detected — falling back to CPU")
            return "cpu"
    except ImportError:
        logger.warning("PyTorch not installed — using CPU")
        return "cpu"
    except Exception as e:
        logger.warning(f"GPU detection error: {e} — using CPU")
        return "cpu"


def get_gpu_info() -> dict:
    """
    Returns detailed GPU information as a dictionary.
    """
    info = {
        "available": False,
        "name": "CPU",
        "vram_gb": 0.0,
        "cuda_version": None,
        "device_count": 0,
    }
    try:
        import torch
        if torch.cuda.is_available():
            info["available"] = True
            info["name"] = torch.cuda.get_device_name(0)
            info["vram_gb"] = round(
                torch.cuda.get_device_properties(0).total_memory / (1024 ** 3), 1
            )
            info["cuda_version"] = torch.version.cuda
            info["device_count"] = torch.cuda.device_count()
    except Exception as e:
        logger.debug(f"Could not retrieve GPU info: {e}")
    return info


def get_half_precision_support(device: str) -> bool:
    """
    Returns True if the device supports float16 half-precision.
    Most modern NVIDIA GPUs support fp16 for faster inference.
    """
    if device == "cpu":
        return False
    try:
        import torch
        cap = torch.cuda.get_device_capability(0)
        # Compute capability 7.0+ (Volta) fully supports fp16
        return cap[0] >= 7
    except Exception:
        return False
