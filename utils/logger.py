"""
Tasklyn — Centralized Logger
=============================
Provides a singleton logger instance used across the entire application.
Writes to both console (colourised) and a rotating file log.
"""
from __future__ import annotations

import logging
import logging.handlers
import sys
from pathlib import Path


# ANSI colour codes for colourised console output
_COLOURS: dict[int, str] = {
    logging.DEBUG:    "\033[36m",   # Cyan
    logging.INFO:     "\033[32m",   # Green
    logging.WARNING:  "\033[33m",   # Yellow
    logging.ERROR:    "\033[31m",   # Red
    logging.CRITICAL: "\033[35m",   # Magenta
}
_RESET = "\033[0m"


class _ColouredFormatter(logging.Formatter):
    """Formatter that prepends ANSI colour codes to levelname on TTY outputs."""

    def format(self, record: logging.LogRecord) -> str:
        colour = _COLOURS.get(record.levelno, "")
        if sys.stderr.isatty():
            record.levelname = f"{colour}{record.levelname}{_RESET}"
        return super().format(record)


def get_logger(name: str = "tasklyn") -> logging.Logger:
    """
    Return (and lazily configure) the named application logger.

    Parameters
    ----------
    name:
        Logger namespace. Use ``__name__`` in each module so log lines
        include the module path (e.g. ``tasklyn.services.task_service``).

    Returns
    -------
    logging.Logger
        Configured logger instance.
    """
    logger = logging.getLogger(name)

    # Only configure handlers once (idempotent)
    if logger.handlers:
        return logger

    # Resolve log level from config lazily to avoid circular imports
    try:
        from config import LOG_FILE, LOG_LEVEL  # type: ignore[import]
        level = getattr(logging, LOG_LEVEL.upper(), logging.INFO)
        log_file: Path = LOG_FILE
    except ImportError:
        level = logging.INFO
        log_file = Path.home() / ".tasklyn" / "tasklyn.log"

    logger.setLevel(level)
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # --- Console handler ---
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(level)
    console_fmt = _ColouredFormatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%H:%M:%S",
    )
    console_handler.setFormatter(console_fmt)
    logger.addHandler(console_handler)

    # --- Rotating file handler (5 MB × 3 backups) ---
    file_handler = logging.handlers.RotatingFileHandler(
        filename=str(log_file),
        maxBytes=5 * 1024 * 1024,
        backupCount=3,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)   # always verbose in file
    file_fmt = logging.Formatter(
        fmt="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_fmt)
    logger.addHandler(file_handler)

    # Prevent propagation to root logger
    logger.propagate = False

    return logger
