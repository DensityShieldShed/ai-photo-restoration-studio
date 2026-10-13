"""Model registry — loads and verifies ONNX weights declared in the manifest.

Integrity: every entry in the manifest carries a SHA256. Loading a model
whose hash does not match raises ``ModelIntegrityError`` and the pipeline
refuses to run. This is the primary supply-chain defense.
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path

from app.services.logging_service import get_logger

LOG = get_logger(__name__)
_CHUNK = 1 << 20


class ModelIntegrityError(RuntimeError):
    """Raised when a model file's SHA256 does not match the manifest."""


@dataclass(frozen=True, slots=True)
class ModelEntry:
    key: str
    filename: str
    sha256: str
    input_size: tuple[int, int]
    scale: int = 1
    precision: str = "fp16"

    @property
    def is_upscaler(self) -> bool:
        return self.scale > 1


class ModelRegistry:
    def __init__(self, root: Path, entries: dict[str, ModelEntry]) -> None:
        self._root = root
        self._entries = entries
        self._sessions: dict[str, object] = {}

    @classmethod
    def from_manifest(cls, manifest_path: Path) -> "ModelRegistry":
        manifest_path = Path(manifest_path)
        data = json.loads(manifest_path.read_text(encoding="utf-8"))
        entries: dict[str, ModelEntry] = {}
        for key, raw in data.get("models", {}).items():
            entries[key] = ModelEntry(
                key=key,
                filename=raw["filename"],
                sha256=raw["sha256"],
                input_size=tuple(raw.get("input_size", (512, 512))),  # type: ignore[arg-type]
                scale=int(raw.get("scale", 1)),
                precision=raw.get("precision", "fp16"),
            )
        LOG.info("registry loaded %d models from %s", len(entries), manifest_path.name)
        return cls(root=manifest_path.parent.parent / "models" / "weights", entries=entries)

    def entry(self, key: str) -> ModelEntry:
        try:
            return self._entries[key]
        except KeyError as exc:
            raise KeyError(f"no model registered under key {key!r}") from exc

    def verify(self, key: str) -> Path:
        entry = self.entry(key)
        path = self._root / entry.filename
        if not path.exists():
            raise FileNotFoundError(f"model file missing: {path}")
        digest = _sha256(path)
        if digest != entry.sha256:
            raise ModelIntegrityError(
                f"{entry.filename} sha256 mismatch: manifest={entry.sha256[:12]}… disk={digest[:12]}…"
            )
        return path

    def session(self, key: str) -> object:
        """Lazy-load an ONNX session. Serialized externally by batch_runner."""
        if key in self._sessions:
            return self._sessions[key]
        path = self.verify(key)
        import onnxruntime as ort

        providers = ort.get_available_providers()
        prefer = [p for p in ("CUDAExecutionProvider", "DmlExecutionProvider") if p in providers]
        prefer.append("CPUExecutionProvider")
        sess = ort.InferenceSession(str(path), providers=prefer)
        self._sessions[key] = sess
        LOG.info("loaded session %s providers=%s", key, sess.get_providers())
        return sess


def _sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(_CHUNK), b""):
            h.update(chunk)
    return h.hexdigest()