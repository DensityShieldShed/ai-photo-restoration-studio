"""Bootstrap entry point for the desktop application.

Launches the Qt shell, wires the restoration engine, and hands control to
``app.ui.main_window``. All heavy work is dispatched off the GUI thread via
``services.batch_runner``.
"""
from __future__ import annotations

import sys
from pathlib import Path

from app.core.engine import RestorationEngine
from app.services.logging_service import configure_logging, get_logger
from app.services.settings_store import SettingsStore
from app.utils.platform_probe import describe_host

LOG = get_logger(__name__)


def _ensure_runtime_dirs(base: Path) -> None:
    for name in ("logs", "temp", "output", "restoration_cache"):
        (base / name).mkdir(parents=True, exist_ok=True)


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv if argv is None else argv)
    from platformdirs import user_data_dir

    data_root = Path(user_data_dir("PhotoRestorationStudio", "RestorationStudio"))
    _ensure_runtime_dirs(data_root)
    configure_logging(data_root / "logs")

    LOG.info("boot %s", describe_host())
    settings = SettingsStore(data_root / "settings.json")
    engine = RestorationEngine(settings=settings, cache_dir=data_root / "restoration_cache")

    try:
        from PySide6.QtWidgets import QApplication

        from app.ui.main_window import MainWindow
    except ImportError as exc:  # pragma: no cover - GUI is optional for CLI users
        LOG.error("PySide6 unavailable: %s", exc)
        return 2

    qt_app = QApplication(argv)
    qt_app.setApplicationName("AI Photo Restoration Studio")
    window = MainWindow(engine=engine, settings=settings)
    window.show()
    return qt_app.exec()


if __name__ == "__main__":
    raise SystemExit(main())