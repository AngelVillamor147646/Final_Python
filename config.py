"""
Tasklyn — Central Application Configuration
============================================
All application-wide constants, paths, and tunable parameters live here.
Nothing should be hardcoded in individual modules.
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Base paths
# ---------------------------------------------------------------------------

# Root of the installed/running application
if getattr(sys, "frozen", False):
    # PyInstaller bundle
    APP_ROOT: Path = Path(sys.executable).parent
else:
    APP_ROOT: Path = Path(__file__).parent.resolve()

# User data lives in the platform home directory so it survives app updates
USER_DATA_DIR: Path = Path.home() / ".tasklyn"
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)

ASSETS_DIR: Path = APP_ROOT / "assets"
FONTS_DIR: Path = ASSETS_DIR / "fonts"
ICONS_DIR: Path = ASSETS_DIR / "icons"
AVATARS_DIR: Path = ASSETS_DIR / "avatars"
IMAGES_DIR: Path = ASSETS_DIR / "images"

STORAGE_DIR: Path = USER_DATA_DIR / "storage"
STORAGE_DIR.mkdir(parents=True, exist_ok=True)

BACKUPS_DIR: Path = USER_DATA_DIR / "backups"
BACKUPS_DIR.mkdir(parents=True, exist_ok=True)

EXPORTS_DIR: Path = USER_DATA_DIR / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# Database
# ---------------------------------------------------------------------------

DATABASE_PATH: Path = USER_DATA_DIR / "tasklyn.db"
DATABASE_VERSION: int = 1  # bump when schema changes

# ---------------------------------------------------------------------------
# Application metadata
# ---------------------------------------------------------------------------

APP_NAME: str = "Tasklyn"
APP_VERSION: str = "1.0.0"
APP_AUTHOR: str = "Tasklyn Dev"
APP_DESCRIPTION: str = "Offline Academic Management System"

# ---------------------------------------------------------------------------
# UI / Theme defaults
# ---------------------------------------------------------------------------

DEFAULT_THEME: str = "Dark"   # "Dark" | "Light"
DEFAULT_PRIMARY_HUE: str = "DeepPurple"
DEFAULT_ACCENT_HUE: str = "Amber"

FONT_REGULAR: str = str(FONTS_DIR / "Inter-Regular.ttf")
FONT_MEDIUM: str = str(FONTS_DIR / "Inter-Medium.ttf")
FONT_BOLD: str = str(FONTS_DIR / "Inter-Bold.ttf")
FONT_MONO: str = str(FONTS_DIR / "RobotoMono-Regular.ttf")

# Fallback to system fonts if custom fonts not present
def _resolve_font(path: str, fallback: str = "Roboto") -> str:
    return path if os.path.exists(path) else fallback

# ---------------------------------------------------------------------------
# Pomodoro defaults
# ---------------------------------------------------------------------------

POMODORO_WORK_MINUTES: int = 25
POMODORO_SHORT_BREAK_MINUTES: int = 5
POMODORO_LONG_BREAK_MINUTES: int = 15
POMODORO_SESSIONS_BEFORE_LONG_BREAK: int = 4

# ---------------------------------------------------------------------------
# Gamification constants
# ---------------------------------------------------------------------------

XP_TASK_COMPLETE: int = 10
XP_TASK_LATE: int = 2
XP_POMODORO_SESSION: int = 5
XP_FLASHCARD_CORRECT: int = 1
XP_STREAK_BONUS_MULTIPLIER: float = 1.5

STREAK_GRACE_HOURS: int = 2          # hours past midnight before streak breaks
ACCOUNTABILITY_SCORE_MAX: float = 100.0

SKILL_SLUGS: list[str] = [
    "time_management",
    "consistency",
    "focus",
    "productivity",
    "discipline",
]

# ---------------------------------------------------------------------------
# Flashcard constraints
# ---------------------------------------------------------------------------

FLASHCARD_MIN_CARDS: int = 20
FLASHCARD_MAX_CARDS: int = 100

# ---------------------------------------------------------------------------
# Notification settings
# ---------------------------------------------------------------------------

NOTIFICATION_APP_NAME: str = APP_NAME
NOTIFICATION_ICON: str = str(ICONS_DIR / "tasklyn_icon.png")

# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_FILE: Path = USER_DATA_DIR / "tasklyn.log"
LOG_LEVEL: str = os.environ.get("TASKLYN_LOG_LEVEL", "INFO")

# ---------------------------------------------------------------------------
# Export / Backup
# ---------------------------------------------------------------------------

BACKUP_MAX_COUNT: int = 10           # keep last N auto-backups
CSV_DATE_FORMAT: str = "%Y-%m-%d"
PDF_PAGE_SIZE: str = "A4"

# ---------------------------------------------------------------------------
# Avatar slugs
# ---------------------------------------------------------------------------

AVATAR_SLUGS: list[str] = [
    "boy_neutral", "boy_smile", "boy_sad", "boy_star",
    "girl_neutral", "girl_smile", "girl_sad", "girl_star",
]

MOOD_THRESHOLDS: dict[str, tuple[float, float]] = {
    # (min_accuracy, max_accuracy) → mood slug suffix
    "sad":     (0.0,  0.40),
    "neutral": (0.40, 0.70),
    "smile":   (0.70, 0.90),
    "star":    (0.90, 1.01),
}
