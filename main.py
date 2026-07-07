"""
Application entry point.
Sets up logging, applies the theme, and launches the main window.
"""
import sys
import os
from pathlib import Path

# ── Ensure project root is in sys.path ─────────────────────────────── #
PROJECT_ROOT = Path(__file__).parent
sys.path.insert(0, str(PROJECT_ROOT))

from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QFontDatabase
from PySide6.QtWidgets import QApplication

from src.core.logger import setup_logging
from src.core.settings import AppSettings
from src.gui.main_window import MainWindow
from src.gui.styles import DARK_THEME


def main():
    # ── Logging ─────────────────────────────────────────────────────── #
    log_dir = PROJECT_ROOT / "logs"
    setup_logging(log_dir)

    import logging
    logger = logging.getLogger(__name__)
    logger.info("Starting AI Image Enhancer")

    # ── Qt Application ───────────────────────────────────────────────── #
    # High-DPI support
    os.environ.setdefault("QT_AUTO_SCREEN_SCALE_FACTOR", "1")

    app = QApplication(sys.argv)
    app.setApplicationName("AI Image Enhancer")
    app.setApplicationVersion("1.0.0")
    app.setOrganizationName("AIEnhancerTeam")

    # ── Font ─────────────────────────────────────────────────────────── #
    font = QFont("Ubuntu", 12)
    font.setStyleStrategy(QFont.PreferAntialias)
    app.setFont(font)

    # ── Dark theme ───────────────────────────────────────────────────── #
    app.setStyleSheet(DARK_THEME)

    # ── Settings ─────────────────────────────────────────────────────── #
    settings = AppSettings()

    # ── Main window ──────────────────────────────────────────────────── #
    window = MainWindow(settings)
    window.show()

    logger.info("Application running")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
