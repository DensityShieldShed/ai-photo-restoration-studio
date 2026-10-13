"""Pipeline — ordered stages that transform an image array end-to-end.

Each stage receives and returns a ``float32`` HWC tensor in [0, 1] with
3 channels. Stages may change spatial dimensions (upscale) but MUST NOT
change channel count or value range. Tiling is delegated to the handler.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import numpy as np

from app.services.logging_service import get_logger

LOG = get_logger(__name__)

Tensor = np.ndarray  # shape (H, W, 3), dtype float32, range [0, 1]


class StageHandler(Protocol):
    name: str
    requires_tiling: bool

    def apply(self, image: Tensor, *, ctx: "StageContext") -> Tensor: ...


@dataclass(slots=True)
class StageContext:
    cache_dir: Path
    stage_index: int = 0
    seed: int = 0
    tile_size: int = 512
    tile_overlap: int = 32
    extras: dict[str, object] = field(default_factory=dict)


@dataclass(slots=True)
class PipelineStage:
    name: str
    handler: StageHandler
    enabled: bool = True


@dataclass(slots=True)
class Pipeline:
    name: str
    stages: list[PipelineStage]
    cache_dir: Path
    _built: bool = False

    def run(self, image: Tensor, *, seed: int = 0) -> Tensor:
        if image.dtype != np.float32:
            raise TypeError(f"pipeline expects float32, got {image.dtype}")
        if image.ndim != 3 or image.shape[2] != 3:
            raise ValueError(f"pipeline expects HWC-3, got shape {image.shape}")
        ctx = StageContext(cache_dir=self.cache_dir, seed=seed)
        current = np.clip(image, 0.0, 1.0)
        for idx, stage in enumerate(self.stages):
            if not stage.enabled:
                continue
            ctx.stage_index = idx
            before = current.shape
            current = stage.handler.apply(current, ctx=ctx)
            LOG.debug(
                "stage=%s in=%s out=%s handler=%s",
                stage.name, before, current.shape, type(stage.handler).__name__,
            )
        return np.clip(current, 0.0, 1.0)


__all__ = ["Pipeline", "PipelineStage", "StageContext", "StageHandler", "Tensor"]