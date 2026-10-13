"""Denoise handler — removes film grain, sensor noise, JPEG blocking.

Uses a small U-Net trained on paired (clean, degraded) scans. Tile-based
because the ONNX graph has fixed 512x512 input.
"""
from __future__ import annotations

import numpy as np

from app.core.pipeline import StageContext, Tensor
from app.core.registry import ModelRegistry
from app.models.tiler import run_tiled
from app.utils.color import to_tensor

MODEL_KEY = "denoise_unet_v3"


class DenoiseHandler:
    name = "denoise"
    requires_tiling = True

    def __init__(self, registry: ModelRegistry, strength: float = 0.8) -> None:
        self._registry = registry
        self._strength = float(np.clip(strength, 0.0, 1.0))

    def apply(self, image: Tensor, *, ctx: StageContext) -> Tensor:
        session = self._registry.session(MODEL_KEY)
        denoised = run_tiled(
            image, session,
            tile=ctx.tile_size, overlap=ctx.tile_overlap,
            pad_mode="reflect",
        )
        # Blend toward original by strength so users can dial grain back in.
        return (self._strength * denoised + (1.0 - self._strength) * image).astype(np.float32)

    def _shape_note(self) -> tuple[int, int]:
        return self._registry.entry(MODEL_KEY).input_size


def to_model_input(image: Tensor) -> np.ndarray:
    """NCHW float32 for the ONNX graph."""
    return to_tensor(image).transpose(2, 0, 1)[None, ...]