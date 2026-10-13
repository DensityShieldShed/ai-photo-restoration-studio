"""Deblur handler — motion and defocus correction via NAFNet-lite.

The model is trained on synthetic blur kernels up to sigma=6. Beyond that
it hallucinates; the handler caps effective sigma and warns.
"""
from __future__ import annotations

import numpy as np

from app.core.pipeline import StageContext, Tensor
from app.core.registry import ModelRegistry
from app.models.tiler import run_tiled
from app.services.logging_service import get_logger
from app.utils.metrics import estimate_blur_sigma

LOG = get_logger(__name__)
MODEL_KEY = "deblur_nafnet_lite"
MAX_SIGMA = 6.0


class DeblurHandler:
    name = "deblur"
    requires_tiling = True

    def __init__(self, registry: ModelRegistry) -> None:
        self._registry = registry

    def apply(self, image: Tensor, *, ctx: StageContext) -> Tensor:
        sigma = estimate_blur_sigma(image)
        if sigma > MAX_SIGMA:
            LOG.warning("estimated sigma=%.2f exceeds model cap %.1f — expect ring artifacts", sigma, MAX_SIGMA)
        session = self._registry.session(MODEL_KEY)
        return run_tiled(
            image, session,
            tile=ctx.tile_size, overlap=ctx.tile_overlap,
            pad_mode="edge",
        ).astype(np.float32)