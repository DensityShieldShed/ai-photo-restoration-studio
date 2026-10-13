"""Restoration engine — owns model registry, cache, and pipeline assembly.

A single engine instance lives for the process lifetime. It is thread-safe
for pipeline construction (immutable after first build) but the underlying
ONNX sessions are NOT thread-safe; concurrent inference must go through
``services.batch_runner`` which serializes per-session calls.
"""
from __future__ import annotations

import threading
from dataclasses import dataclass, field
from pathlib import Path

from app.core.pipeline import Pipeline, PipelineStage
from app.core.registry import ModelRegistry
from app.handlers import build_default_handlers
from app.services.logging_service import get_logger
from app.services.settings_store import SettingsStore

LOG = get_logger(__name__)


@dataclass(slots=True)
class EngineMetrics:
    images_processed: int = 0
    tiles_processed: int = 0
    total_ms: float = 0.0
    per_stage_ms: dict[str, float] = field(default_factory=dict)


class RestorationEngine:
    """Assembles pipelines from registered handlers and dispatches inference."""

    def __init__(self, settings: SettingsStore, cache_dir: Path) -> None:
        self._settings = settings
        self._cache_dir = cache_dir
        self._lock = threading.RLock()
        self._presets: dict[str, Pipeline] = {}
        self._registry = ModelRegistry.from_manifest(settings.model_manifest_path)
        self._metrics = EngineMetrics()
        self._handlers = build_default_handlers(self._registry)

    @property
    def metrics(self) -> EngineMetrics:
        return self._metrics

    @property
    def registry(self) -> ModelRegistry:
        return self._registry

    def available_presets(self) -> list[str]:
        return sorted(self._presets.keys()) or ["default", "archival", "portrait", "print"]

    def pipeline_for_preset(self, preset: str) -> Pipeline:
        with self._lock:
            if preset in self._presets:
                return self._presets[preset]
            stages = self._stages_for_preset(preset)
            pipeline = Pipeline(name=preset, stages=stages, cache_dir=self._cache_dir)
            self._presets[preset] = pipeline
            LOG.info("assembled preset=%s stages=%s", preset, [s.name for s in stages])
            return pipeline

    def _stages_for_preset(self, preset: str) -> list[PipelineStage]:
        if preset == "archival":
            order = ("denoise", "scratch_repair", "deblur", "colorize", "upscale")
        elif preset == "portrait":
            order = ("face_restore", "denoise", "colorize", "upscale_soft")
        elif preset == "print":
            order = ("denoise", "deblur", "upscale", "sharpen")
        else:
            order = ("denoise", "deblur", "colorize", "upscale")
        return [PipelineStage(name=n, handler=self._handlers[n]) for n in order if n in self._handlers]

    def record(self, *, tiles: int, elapsed_ms: float, stage: str) -> None:
        with self._lock:
            self._metrics.images_processed += 1
            self._metrics.tiles_processed += tiles
            self._metrics.total_ms += elapsed_ms
            self._metrics.per_stage_ms[stage] = self._metrics.per_stage_ms.get(stage, 0.0) + elapsed_ms