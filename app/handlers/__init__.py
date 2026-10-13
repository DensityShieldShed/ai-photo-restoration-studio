"""Feature handlers — one module per restoration capability.

Each handler module exposes a ``HANDLER`` singleton implementing
``core.pipeline.StageHandler``. ``build_default_handlers`` wires them
against the model registry by key.
"""
from __future__ import annotations

from app.core.registry import ModelRegistry
from app.handlers.colorize import ColorizeHandler
from app.handlers.deblur import DeblurHandler
from app.handlers.denoise import DenoiseHandler
from app.handlers.face_restore import FaceRestoreHandler
from app.handlers.scratch_repair import ScratchRepairHandler
from app.handlers.sharpen import SharpenHandler
from app.handlers.upscale import UpscaleHandler

HandlerMap = dict[str, object]


def build_default_handlers(registry: ModelRegistry) -> HandlerMap:
    return {
        "denoise": DenoiseHandler(registry),
        "deblur": DeblurHandler(registry),
        "colorize": ColorizeHandler(registry),
        "upscale": UpscaleHandler(registry, scale=4),
        "upscale_soft": UpscaleHandler(registry, scale=2),
        "face_restore": FaceRestoreHandler(registry),
        "scratch_repair": ScratchRepairHandler(registry),
        "sharpen": SharpenHandler(registry),
    }


__all__ = ["build_default_handlers", "HandlerMap"]