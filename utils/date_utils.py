"""
Tasklyn — Date / Time Utilities
=================================
All date arithmetic, formatting helpers, and timezone-aware helpers used
across the application. Uses only the stdlib so there are no extra deps.
"""
from __future__ import annotations

from datetime import date, datetime, time, timedelta
from typing import Optional


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

DATE_FMT = "%Y-%m-%d"
TIME_FMT = "%H:%M"
DATETIME_FMT = "%Y-%m-%d %H:%M"
DISPLAY_DATE_FMT = "%d %b %Y"          # e.g. 23 Sep 2026
DISPLAY_DATETIME_FMT = "%d %b %Y %H:%M"


def fmt_date(d: date | datetime | None) -> str:
    """Return ISO date string or empty string for None."""
    if d is None:
        return ""
    if isinstance(d, datetime):
        return d.strftime(DATE_FMT)
    return d.strftime(DATE_FMT)


def fmt_time(t: time | datetime | None) -> str:
    """Return HH:MM string or empty string for None."""
    if t is None:
        return ""
    return t.strftime(TIME_FMT)


def fmt_datetime(dt: datetime | None) -> str:
    """Return ISO datetime string or empty string for None."""
    if dt is None:
        return ""
    return dt.strftime(DATETIME_FMT)


def display_date(d: date | datetime | None) -> str:
    """Return human-friendly date like '23 Sep 2026'."""
    if d is None:
        return ""
    if isinstance(d, datetime):
        return d.strftime(DISPLAY_DATE_FMT)
    return d.strftime(DISPLAY_DATE_FMT)


def display_datetime(dt: datetime | None) -> str:
    """Return human-friendly datetime like '23 Sep 2026 14:30'."""
    if dt is None:
        return ""
    return dt.strftime(DISPLAY_DATETIME_FMT)


# ---------------------------------------------------------------------------
# Parsing
# ---------------------------------------------------------------------------

def parse_date(s: str) -> Optional[date]:
    """Parse ISO date string; returns None on failure."""
    try:
        return datetime.strptime(s.strip(), DATE_FMT).date()
    except (ValueError, AttributeError):
        return None


def parse_time(s: str) -> Optional[time]:
    """Parse HH:MM string; returns None on failure."""
    try:
        return datetime.strptime(s.strip(), TIME_FMT).time()
    except (ValueError, AttributeError):
        return None


def parse_datetime(s: str) -> Optional[datetime]:
    """Parse ISO datetime string; returns None on failure."""
    try:
        return datetime.strptime(s.strip(), DATETIME_FMT)
    except (ValueError, AttributeError):
        return None


# ---------------------------------------------------------------------------
# Convenience helpers
# ---------------------------------------------------------------------------

def today() -> date:
    """Return today's local date."""
    return date.today()


def now() -> datetime:
    """Return current local datetime (no tzinfo)."""
    return datetime.now()


def start_of_week(d: date | None = None) -> date:
    """Return Monday of the week containing *d* (default: today)."""
    d = d or today()
    return d - timedelta(days=d.weekday())


def end_of_week(d: date | None = None) -> date:
    """Return Sunday of the week containing *d* (default: today)."""
    return start_of_week(d) + timedelta(days=6)


def start_of_month(d: date | None = None) -> date:
    """Return first day of the month containing *d*."""
    d = d or today()
    return d.replace(day=1)


def end_of_month(d: date | None = None) -> date:
    """Return last day of the month containing *d*."""
    d = d or today()
    # Go to first of next month then back one day
    if d.month == 12:
        return d.replace(day=31)
    return d.replace(month=d.month + 1, day=1) - timedelta(days=1)


def days_until(target: date | datetime) -> int:
    """Return number of days from today until *target* (negative if past)."""
    if isinstance(target, datetime):
        target = target.date()
    return (target - today()).days


def is_today(d: date | datetime) -> bool:
    if isinstance(d, datetime):
        d = d.date()
    return d == today()


def is_overdue(deadline: date | datetime) -> bool:
    """Return True if deadline is strictly in the past."""
    if isinstance(deadline, datetime):
        return deadline < now()
    return deadline < today()


def week_dates(reference: date | None = None) -> list[date]:
    """Return list of 7 dates (Mon–Sun) for the week containing *reference*."""
    start = start_of_week(reference)
    return [start + timedelta(days=i) for i in range(7)]


def day_name(d: date) -> str:
    """Return abbreviated weekday name, e.g. 'Mon'."""
    return d.strftime("%a")


def time_range_overlaps(
    start1: time, end1: time,
    start2: time, end2: time,
) -> bool:
    """
    Return True if two half-open time intervals [start1, end1) and
    [start2, end2) overlap.
    """
    return start1 < end2 and start2 < end1


def duration_minutes(start: time, end: time) -> int:
    """Return duration in minutes between two times (same day assumed)."""
    s = datetime.combine(date.today(), start)
    e = datetime.combine(date.today(), end)
    return max(0, int((e - s).total_seconds() // 60))


def minutes_to_hm(minutes: int) -> str:
    """Convert integer minutes to 'Xh Ym' string."""
    h, m = divmod(minutes, 60)
    if h and m:
        return f"{h}h {m}m"
    if h:
        return f"{h}h"
    return f"{m}m"


def iso_week_number(d: date | None = None) -> int:
    """Return ISO week number (1–53) for *d*."""
    return (d or today()).isocalendar()[1]
