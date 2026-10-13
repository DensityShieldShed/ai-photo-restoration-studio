"""Sharpen handler — final unsharp mask tuned for print output.

Not a model. A deterministic post-process so the print preset lands with
crisp edges without an extra ONNX pass. Radius and amount come from the
preset; defaults target 300dpi A4.
"""
from __future__ import annotations

import cv2
import numpy as np

from app.core.pipeline import StageContext, Tensor
from app.core.registry import ModelRegistry


class SharpenHandler:
    name = "sharpen"
    requires_tiling = False

    def __init__(self, registry: ModelRegistry, radius: float = 1.6, amount: float = 0.7) -> None:
        self._registry = registry
        self._radius = float(radius)
        self._amount = float(amount)

    def apply(self, image: Tensor, *, ctx: StageContext) -> Tensor:
        u8 = (np.clip(image, 0, 1) * 255.0).astype(np.uint8)
        blurred = cv2.GaussianBlur(u8, (0, 0), sigmaX=self._radius)
        sharpened = cv2.addWeighted(u8,