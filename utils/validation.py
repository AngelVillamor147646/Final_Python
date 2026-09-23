"""
Tasklyn — Input Validation Utilities
======================================
Centralised validation functions used by services and UI before persisting
data.  All functions return a ``(is_valid: bool, error_message: str)`` tuple
so callers can display the error message directly in the UI.
"""
from __future__ import annotations

import re
from datetime import date, datetime, time
from typing import Any, Optional


ValidationResult = tuple[bool, str]   # (ok, error_message)

# ---------------------------------------------------------------------------
# Generic helpers
# ---------------------------------------------------------------------------

def ok() -> ValidationResult:
    return True, ""


def err(msg: str) -> ValidationResult:
    return False, msg


# ---------------------------------------------------------------------------
# String / text
# ---------------------------------------------------------------------------

def validate_required(value: Any, field: str = "Field") -> ValidationResult:
    """Fail if *value* is None, empty string, or whitespace-only."""
    if value is None or str(value).strip() == "":
        return err(f"{field} is required.")
    return ok()


def validate_length(
    value: str,
    field: str = "Field",
    min_len: int = 1,
    max_len: int = 255,
) -> ValidationResult:
    length = len(value.strip())
    if length < min_len:
        return err(f"{field} must be at least {min_len} character(s).")
    if length > max_len:
        return err(f"{field} must not exceed {max_len} characters.")
    return ok()


def validate_name(name: str, field: str = "Name") -> ValidationResult:
    """Validate a human name / title (2–100 chars, no special injection chars)."""
    v, msg = validate_required(name, field)
    if not v:
        return v, msg
    name = name.strip()
    if len(name) < 2:
        return err(f"{field} must be at least 2 characters.")
    if len(name) > 100:
        return err(f"{field} must not exceed 100 characters.")
    # Disallow SQL/script injection characters
    dangerous = re.compile(r"[<>\"'%;()&+]")
    if dangerous.search(name):
        return err(f"{field} contains invalid characters.")
    return ok()


# ---------------------------------------------------------------------------
# Numeric
# ---------------------------------------------------------------------------

def validate_positive_int(value: Any, field: str = "Value") -> ValidationResult:
    try:
        v = int(value)
    except (TypeError, ValueError):
        return err(f"{field} must be a whole number.")
    if v < 1:
        return err(f"{field} must be greater than zero.")
    return ok()


def validate_range(
    value: Any,
    min_val: float,
    max_val: float,
    field: str = "Value",
) -> ValidationResult:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return err(f"{field} must be a number.")
    if not (min_val <= v <= max_val):
        return err(f"{field} must be between {min_val} and {max_val}.")
    return ok()


# ---------------------------------------------------------------------------
# Date / time
# ---------------------------------------------------------------------------

def validate_date_not_past(
    d: date | datetime | str | None,
    field: str = "Date",
    allow_today: bool = True,
) -> ValidationResult:
    if d is None:
        return err(f"{field} is required.")
    if isinstance(d, str):
        from utils.date_utils import parse_date
        parsed = parse_date(d)
        if parsed is None:
            return err(f"{field} is not a valid date (expected YYYY-MM-DD).")
        d = parsed
    if isinstance(d, datetime):
        d = d.date()
    today = date.today()
    if allow_today:
        if d < today:
            return err(f"{field} cannot be in the past.")
    else:
        if d <= today:
            return err(f"{field} must be a future date.")
    return ok()


def validate_time_order(
    start: time | str | None,
    end: time | str | None,
    start_field: str = "Start time",
    end_field: str = "End time",
) -> ValidationResult:
    """Ensure start < end."""
    if start is None:
        return err(f"{start_field} is required.")
    if end is None:
        return err(f"{end_field} is required.")
    if isinstance(start, str):
        from utils.date_utils import parse_time
        start = parse_time(start)
    if isinstance(end, str):
        from utils.date_utils import parse_time
        end = parse_time(end)
    if start is None or end is None:
        return err("Time must be in HH:MM format.")
    if start >= end:
        return err(f"{start_field} must be before {end_field}.")
    return ok()


# ---------------------------------------------------------------------------
# Colour
# ---------------------------------------------------------------------------

HEX_COLOUR_RE = re.compile(r"^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$")


def validate_hex_colour(colour: str, field: str = "Colour") -> ValidationResult:
    if not HEX_COLOUR_RE.match(colour or ""):
        return err(f"{field} must be a valid hex colour (e.g. #FF5733).")
    return ok()


# ---------------------------------------------------------------------------
# File / path
# ---------------------------------------------------------------------------

def validate_file_extension(
    path: str,
    allowed: list[str],
    field: str = "File",
) -> ValidationResult:
    """Check that *path* has one of the *allowed* extensions (case-insensitive)."""
    lower = (path or "").lower()
    if not any(lower.endswith(ext.lower()) for ext in allowed):
        return err(f"{field} must be one of: {', '.join(allowed)}")
    return ok()


# ---------------------------------------------------------------------------
# Flashcard-specific
# ---------------------------------------------------------------------------

def validate_card_count(count: int) -> ValidationResult:
    from config import FLASHCARD_MIN_CARDS, FLASHCARD_MAX_CARDS  # type: ignore
    if count < FLASHCARD_MIN_CARDS:
        return err(
            f"Deck must contain at least {FLASHCARD_MIN_CARDS} cards "
            f"(found {count})."
        )
    if count > FLASHCARD_MAX_CARDS:
        return err(
            f"Deck must not exceed {FLASHCARD_MAX_CARDS} cards "
            f"(found {count})."
        )
    return ok()


# ---------------------------------------------------------------------------
# Markdown safety
# ---------------------------------------------------------------------------

# Very lightweight: strip script tags and javascript: hrefs
_SCRIPT_TAG_RE = re.compile(r"<script[^>]*>.*?</script>", re.IGNORECASE | re.DOTALL)
_JS_HREF_RE = re.compile(r"href\s*=\s*[\"']?javascript:", re.IGNORECASE)


def sanitize_markdown(text: str) -> str:
    """
    Remove obviously dangerous content from user-provided Markdown.
    This is a lightweight safeguard — not a full HTML sanitiser.
    """
    text = _SCRIPT_TAG_RE.sub("", text)
    text = _JS_HREF_RE.sub('href="#"', text)
    return text
