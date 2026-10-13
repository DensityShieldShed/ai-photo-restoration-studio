"""Headless CLI — batch-restore a folder without opening the GUI.

    photo-restore restore C:\\scans --preset archival --out C:\\restored
"""
from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console

from app.core.engine import RestorationEngine
from app.core.pipeline import Pipeline
from app.services.batch_runner import run_batch
from app.services.settings_store import SettingsStore

app = typer.Typer(add_completion=False, help="AI Photo Restoration Studio CLI")
console = Console()


@app.command()
def restore(
    source: Path = typer.Argument(..., exists=True, file_okay=False, readable=True),
    out: Path = typer.Option(Path("output"), "--out", "-o"),
    preset: str = typer.Option("default", "--preset", "-p"),
    recursive: bool = typer.Option(True, "--recursive/--no-recursive"),
) -> None:
    """Restore every supported image under SOURCE using PRESET."""
    settings = SettingsStore.in_memory()
    engine = RestorationEngine(settings=settings, cache_dir=Path("restoration_cache"))
    pipeline = engine.pipeline_for_preset(preset)
    results = run_batch(source, out, pipeline, recursive=recursive, on_progress=_print_progress)
    ok = sum(1 for r in results if r.ok)
    console.print(f"[bold green]{ok}[/] / {len(results)} restored -> {out}")


def _print_progress(done: int, total: int, name: str) -> None:
    console.print(f"[dim]{done}/{total}[/] {name}")


def main() -> None:  # pragma: no cover - thin shim
    app()


__all__ = ["app", "main", "restore"]