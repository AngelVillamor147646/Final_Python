"""Streak service — daily activity recording and streak calculation."""
from __future__ import annotations
from database.repositories import StreakRepository
from utils.logger import get_logger

log = get_logger(__name__)
_repo = StreakRepository()


def record_activity(user_id: int) -> bool:
    """Record today's activity. Returns True if new streak day."""
    is_new = _repo.record_today(user_id, "daily")
    if is_new:
        from services.notification_service import send_notification
        streak = _repo.current_streak(user_id)
        if streak > 0:
            send_notification("🔥 Streak Extended!", f"You're on a {streak} day streak!")
    return is_new


def get_current_streak(user_id: int) -> int:
    return _repo.current_streak(user_id)


def get_longest_streak(user_id: int) -> int:
    return _repo.longest_streak(user_id)


def get_total_active_days(user_id: int) -> int:
    return _repo.total_active_days(user_id)


def get_calendar_data(user_id: int, year: int, month: int) -> list[str]:
    return _repo.get_calendar_data(user_id, year, month)


def missed_yesterday(user_id: int) -> bool:
    return _repo.missed_yesterday(user_id)


def get_streak_summary(user_id: int) -> dict:
    return {
        "current": get_current_streak(user_id),
        "longest": get_longest_streak(user_id),
        "total_days": get_total_active_days(user_id),
        "missed_yesterday": missed_yesterday(user_id),
    }
