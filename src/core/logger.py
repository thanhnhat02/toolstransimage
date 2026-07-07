"""
Centralised logging configuration.
Creates rotating file handler + colored console handler.
"""
import logging
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path


class _ColorFormatter(logging.Formatter):
    """ANSI color codes for terminal output."""

    COLORS = {
        logging.DEBUG: "\033[37m",      # White
        logging.INFO: "\033[36m",       # Cyan
        logging.WARNING: "\033[33m",    # Yellow
        logging.ERROR: "\033[31m",      # Red
        logging.CRITICAL: "\033[35m",   # Magenta
    }
    RESET = "\033[0m"

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelno, self.RESET)
        record.levelname = f"{color}{record.levelname:<8}{self.RESET}"
        return super().format(record)


def setup_logging(
    log_dir: Path,
    level: int = logging.DEBUG,
    console_level: int = logging.INFO,
) -> Path:
    """
    Configure application-wide logging.

    Args:
        log_dir:       Directory where log files are stored.
        level:         File log level (default DEBUG).
        console_level: Console log level (default INFO).

    Returns:
        Path to the created log file.
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"enhancer_{timestamp}.log"

    root = logging.getLogger()
    root.setLevel(level)

    # ── File handler (full detail) ──────────────────────────────────── #
    file_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    fh = RotatingFileHandler(
        log_file, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    fh.setLevel(level)
    fh.setFormatter(file_fmt)
    root.addHandler(fh)

    # ── Console handler (colored, less verbose) ─────────────────────── #
    console_fmt = _ColorFormatter(
        "%(asctime)s %(levelname)s %(name)s  %(message)s",
        datefmt="%H:%M:%S",
    )
    ch = logging.StreamHandler(sys.stdout)
    ch.setLevel(console_level)
    ch.setFormatter(console_fmt)
    root.addHandler(ch)

    logging.getLogger("PIL").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)

    logging.info(f"Logging initialised → {log_file}")
    return log_file
