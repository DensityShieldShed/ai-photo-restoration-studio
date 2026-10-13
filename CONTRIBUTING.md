# Contributing to AI Photo Restoration Studio

Thanks for wanting to help restore old photos. This project is a Windows
desktop tool that runs local ONNX models for denoising, deblurring,
colorization, and upscaling — no cloud, no telemetry, no data leaving
the user's machine.

## Development Setup

1. Install Python 3.11 or 3.12 (3.10 works but is EOL-adjacent).
2. Create a venv: `python -m venv .venv && .venv\Scripts\activate`
3. Install deps: `pip install -r requirements.txt`
4. Install dev deps: `pip install -r requirements-dev.txt`
5. Run the app: `python -m app.main`
6. Run tests: `pytest -q`

## Architecture Overview

```
app/                entry + bootstrap + Qt shell
  core/             restoration engine, pipeline, model registry
  handlers/         per-feature handlers (denoise, colorize, upscale, ...)
  services/         IO, batching, export, telemetry-free logging
  models/           ONNX model wrappers + tile scheduling
  utils/            image helpers, EXIF, color spaces, cli
config/             default config + presets
tests/              pytest suite
```

Handlers register themselves against the pipeline via
`handlers.registry.register`. Adding a new restoration feature means
dropping a new handler module in `app/handlers/` and adding one line to
`app/handlers/__init__.py`.

## Coding Standards

- Black + Ruff. Line length 100. Run `ruff check .` before committing.
- Type hints on every public function. `mypy --strict` on `app/core`.
- No blocking calls on the Qt main thread. Long work goes through
  `services.batch_runner`.
- Logging via `services.logging_service.get_logger(__name__)`. No `print`.

## Model Contributions

Models live under `models/weights/` and are referenced by hash in
`config/model_manifest.json`. Do not commit weights > 50 MB — use the
release asset channel and pin the SHA256 in the manifest.

## Pull Requests

- One feature per PR.
- Include a test that exercises the new handler on `tests/fixtures/`.
- Update `CHANGELOG.md` under `## Unreleased`.
- Sign-off required (DCO).

## Reporting Bugs

Open an issue with: OS build, GPU model (if any), ONNX Runtime version,
input image dimensions, and the exact preset used. Attach the
`logs/last_run.json` if you're comfortable sharing it — it contains no
pixels, only timings and model hashes.