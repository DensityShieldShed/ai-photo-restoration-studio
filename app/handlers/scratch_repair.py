"""Scratch-repair handler — inpainting for dust, hairs, and tears.

A mask is derived from a per-pixel artifact score; masked regions are
inpainted with a LaMa-style ONNX model. Non-masked pixels are passed
through untouched so the repair stays honest.
"""
from __future__ import annotations

import numpy as np

from app.core.pipeline import StageContext, Tensor
from app.core.registry import ModelRegistry
from app.utils.artifacts import scratch_mask

MODEL_KEY = "inpaint_lama_lite"


class ScratchRepairHandler:
    name = "scratch_repair"
    requires_tiling = False

    def __init__(self, registry: ModelRegistry, threshold: float = 0.35) -> None:
        self._registry = registry
        self._threshold = float(threshold)

    def apply(self, image: Tensor, *, ctx: StageContext) -> Tensor:
        mask = scratch_mask(image, threshold=self._threshold)
        if mask.sum() < 16:
            return image
        session = self._registry.session(MODEL_KEY)
        inpainted = _run_inpaint(session, image, mask)
        keep = (1.0 - mask[..., None]).astype(np.float32)
        return np.clip(inpainted * mask[..., None] + image * keep, 0.0, 1.0).astype(np.float32)


def _run_inpaint(session: object, image: Tensor, mask: np.ndarray) -> Tensor:
    import onnxruntime as ort

    batch = np.concatenate([image.transpose(2, 0, 1), mask[None, ...]], axis=0)[None, ...].astype(np.float32)
    name = session.get_inputs()[0].name  # type: ignore[attr-defined]
    out = session.run(None, {name: batch})[0]  # type: ignore[attr-defined]
    return np.clip(out[0].transpose(1, 2, 0), 0.0, 1.0).astype(np.float32)


__all__ = ["ScratchRepairHandler"]