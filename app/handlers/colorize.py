"""Colorize handler — 1-channel -> 3-channel via a Lab-space CIE network.

Input luminance is taken as L*; the model predicts a* and b*. We clip the
predicted chroma to avoid the "neon grass" failure mode on old B&W scans.
"""
from __future__ import annotations

import numpy as np

from app.core.pipeline import StageContext, Tensor
from app.core.registry import ModelRegistry
from app.models.tiler import run_tiled
from app.utils.color import lab_to_rgb, rgb_to_lab

MODEL_KEY = "colorize_ecnn_v2"
CHROMA_CLIP = 60.0  # Lab b* is unbounded; 60 keeps things believable


class ColorizeHandler:
    name = "colorize"
    requires_tiling = True

    def __init__(self, registry: ModelRegistry, saturation: float = 1.0) -> None:
        self._registry = registry
        self._saturation = float(saturation)

    def apply(self, image: Tensor, *, ctx: StageContext) -> Tensor:
        lab = rgb_to_lab(image)
        l_channel = lab[..., 0:1]
        session = self._registry.session(MODEL_KEY)
        ab = run_tiled(l_channel, session, tile=ctx.tile_size, overlap=ctx.tile_overlap, pad_mode="reflect")
        ab = np.clip(ab, -CHROMA_CLIP, CHROMA_CLIP) * self._saturation
        restored = np.concatenate([l_channel, ab], axis=-1)
        return lab_to_rgb(restored).astype(np.float32)