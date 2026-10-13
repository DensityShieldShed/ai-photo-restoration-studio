"""Upscale handler — Real-ESRGAN-style generator with configurable scale.

Scale 2 uses the "soft" weights tuned for portraits; scale 4 uses the
general weights. Both are tiled because 4K outputs won't fit in a single
forward pass on consumer VRAM.
"""
from __future__ import annotations

import numpy as np

from app.core.pipeline import StageContext, Tensor
from app.core.registry import ModelRegistry
from app.models.tiler import run_tiled
from app.services.logging_service import get_logger

LOG = get_logger(__name__)


class UpscaleHandler:
    name = "upscale"
    requires_tiling = True

    def __init__(self, registry: ModelRegistry, scale: int = 4) -> None:
        if scale not in (2, 4):
            raise ValueError("scale must be 2 or 4")
        self._registry = registry
        self._scale = scale
        self._model_key = f"upscale_x{scale}"

    def apply(self, image: Tensor, *, ctx: StageContext) -> Tensor:
        session = self._registry.session(self._model_key)
        out = run_tiled(
            image, session,
            tile=ctx.tile_size, overlap=ctx.tile_overlap,
            pad_mode="reflect",
            output_scale=self._scale,
        )
        return out.astype(np.float32)


__all__ = ["UpscaleHandler"]