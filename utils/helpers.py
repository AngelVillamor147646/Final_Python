"""
Tasklyn — General Helper Utilities
=====================================
Small, pure functions that don't belong to a more specific utility module.
"""
from __future__ import annotations

import hashlib
import json
import os
import platform
import re
import uuid
from pathlib import Path
from typing import Any


# ---------------------------------------------------------------------------
# ID generation
# ---------------------------------------------------------------------------

def new_uuid() -> str:
    """Return a lowercase UUID4 string."""
    return str(uuid.uuid4())


# ---------------------------------------------------------------------------
# String helpers
# ---------------------------------------------------------------------------

def slugify(text: str) -> str:
    """
    Convert *text* to a URL/filename-safe slug.

    Example: ``"Time Management!"`` → ``"time_management"``
    """
    text = text.lower().strip()
    text = re.sub(r"[^\w\s-]", "", text)
    text = re.sub(r"[\s-]+", "_", text)
    return text


def truncate(text: str, max_len: int = 60, suffix: str = "…") -> str:
    """Truncate *text* to *max_len* characters, appending *suffix* if truncated."""
    if len(text) <= max_len:
        return text
    return text[: max_len - len(suffix)] + suffix


def pluralise(count: int, singular: str, plural: str | None = None) -> str:
    """Return ``'1 task'`` or ``'3 tasks'``."""
    plural = plural or singular + "s"
    return f"{count} {singular if count == 1 else plural}"


def initials(name: str, max_chars: int = 2) -> str:
    """Return uppercase initials from a full name (e.g. 'John Doe' → 'JD')."""
    words = name.strip().split()
    return "".join(w[0].upper() for w in words[:max_chars])


def hex_to_kivy_colour(hex_colour: str) -> list[float]:
    """
    Convert a CSS hex colour string to a Kivy RGBA list (0.0–1.0).

    Supports #RGB and #RRGGBB formats.
    """
    hex_colour = hex_colour.lstrip("#")
    if len(hex_colour) == 3:
        hex_colour = "".join(c * 2 for c in hex_colour)
    r, g, b = (int(hex_colour[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
    return [r, g, b, 1.0]


def kivy_colour_to_hex(rgba: list[float]) -> str:
    """Convert a Kivy RGBA list back to ``#RRGGBB`` hex string."""
    r, g, b = (int(c * 255) for c in rgba[:3])
    return f"#{r:02X}{g:02X}{b:02X}"


# ---------------------------------------------------------------------------
# JSON helpers
# ---------------------------------------------------------------------------

def safe_json_loads(text: str | None, default: Any = None) -> Any:
    """Load JSON from *text*, returning *default* on any parse error."""
    if not text:
        return default
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return default


def safe_json_dumps(obj: Any) -> str:
    """Serialize *obj* to JSON string, returning '{}' on failure."""
    try:
        return json.dumps(obj, ensure_ascii=False)
    except (TypeError, ValueError):
        return "{}"


# ---------------------------------------------------------------------------
# File / path helpers
# ---------------------------------------------------------------------------

def ensure_dir(path: str | Path) -> Path:
    """Create directory (and parents) if it doesn't exist; return Path."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def file_checksum(path: str | Path) -> str:
    """Return SHA-256 hex digest of a file's contents."""
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def safe_filename(name: str) -> str:
    """Strip characters illegal in filenames on Windows/Linux/macOS."""
    return re.sub(r'[\\/:*?"<>|]', "_", name)


# ---------------------------------------------------------------------------
# Platform helpers
# ---------------------------------------------------------------------------

def is_android() -> bool:
    """Return True when running on Android (Buildozer/p4a environment)."""
    return "ANDROID_ARGUMENT" in os.environ


def is_windows() -> bool:
    return platform.system() == "Windows"


def is_macos() -> bool:
    return platform.system() == "Darwin"


def is_linux() -> bool:
    return platform.system() == "Linux"


# ---------------------------------------------------------------------------
# Number helpers
# ---------------------------------------------------------------------------

def clamp(value: float, lo: float, hi: float) -> float:
    """Clamp *value* to the range [*lo*, *hi*]."""
    return max(lo, min(hi, value))


def percentage(part: float, total: float, decimals: int = 1) -> float:
    """Return (part / total) × 100, safely handling zero total."""
    if total == 0:
        return 0.0
    return round((part / total) * 100, decimals)


def lerp(a: float, b: float, t: float) -> float:
    """Linear interpolation between *a* and *b* by factor *t* ∈ [0, 1]."""
    return a + (b - a) * clamp(t, 0.0, 1.0)

# ---------------------------------------------------------------------------
# Snackbar helper for KivyMD 1.2.0
# ---------------------------------------------------------------------------
from kivymd.uix.snackbar import Snackbar as KivyMDSnackbar
from kivymd.uix.label import MDLabel

class TasklynSnackbar:
    COLORS = {
        "success": [0.298, 0.686, 0.313, 1], # #4CAF50
        "error": [0.956, 0.262, 0.211, 1],   # #F44336
        "warning": [1.0, 0.596, 0.0, 1],     # #FF9800
        "info": [0.129, 0.588, 0.952, 1],    # #2196F3
    }
    
    ICONS = {
        "success": "check-circle",
        "error": "alert-circle",
        "warning": "alert",
        "info": "information",
    }

    def __init__(self, text="", notif_type="info"):
        from kivymd.uix.boxlayout import MDBoxLayout
        from kivymd.uix.label import MDIcon
        
        bg_color = self.COLORS.get(notif_type, self.COLORS["info"])
        icon_name = self.ICONS.get(notif_type, self.ICONS["info"])
        
        content = MDBoxLayout(orientation="horizontal", spacing="12dp", padding="8dp")
        content.add_widget(MDIcon(icon=icon_name, theme_text_color="Custom", text_color=(1,1,1,1)))
        content.add_widget(MDLabel(text=str(text), theme_text_color="Custom", text_color=(1,1,1,1)))
        
        self.snackbar = KivyMDSnackbar(
            content,
            md_bg_color=bg_color,
            radius=[8, 8, 8, 8]
        )
        
    def open(self):
        self.snackbar.open()
