"""Face-restore handler — GFPGAN-class face prior for old portraits.

Detects faces with a lightweight ONNX detector, then runs the restore
model only on the face crops before pasting back with a feathered mask.
Whole-image restore on a group photo blows out the background, so we
crop.
"""
from __future__ import annotations

import numpy as np

from app.core.pipeline import StageContext, Tensor
from app.core.registry import ModelRegistry
from app.models.face_detect import detect_faces
from app.models.tiler import run_tiled
from app.services.logging_service import get_logger
from app.utils.mask import feather_mask

LOG = get_logger(__name__)
MODEL_KEY = "face_restore_gfpgan_lite"
FEATHER_PX = 12


class FaceRestoreHandler:
    name = "face_restore"
    requires_tiling = False

    def __init__(self, registry: ModelRegistry) -> None:
        self._registry = registry

    def apply(self, image: Tensor, *, ctx: StageContext) -> Tensor:
        faces = detect_faces(image)
        if not faces:
            LOG.debug("face_restore: no faces detected, passthrough")
            return image
        session = self._registry.session(MODEL_KEY)
        canvas = image.copy()
        for det in faces:
            crop = image[det.y0:det.y1, det.x0:det.x1]
            restored = run_tiled(crop, session, tile=256, overlap=16, pad_mode="edge")
            mask = feather_mask(restored.shape[:2], FEATHER_PX)
            canvas[det.y0:det.y1, det.x0:det.x1] = (
                restored * mask[..., None] + crop * (1.0 - mask[..., None])
            )
        return np.clip(canvas, 0.0, 1.0).astype(np.float32)