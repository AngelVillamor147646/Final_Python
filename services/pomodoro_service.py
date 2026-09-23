"""Pomodoro service — timer logic, session management, statistics."""
from __future__ import annotations
from typing import Optional
from database.repositories import PomodoroRepository, SubjectRepository
from models import PomodoroSession
from utils.logger import get_logger
from utils import today, fmt_date, start_of_week, end_of_week, minutes_to_hm

log = get_logger(__name__)
_repo = PomodoroRepository()


def start_session(user_id: int, work_min: int = 25, break_min: int = 5,
                  subject_id=None, task_id=None) -> PomodoroSession:
    return _repo.create_session(user_id, work_min, break_min, subject_id, task_id)


def complete_session(session_id: int, user_id: int,
                     interruptions: int = 0, notes: str = "") -> list[str]:
    """Complete session; award XP & check badges; return unlocked badge slugs."""
    _repo.complete_session(session_id, interruptions, notes)
    from services.gamification_service import award_xp, check_and_unlock_badges
    from config import XP_POMODORO_SESSION
    award_xp(user_id, "focus", XP_POMODORO_SESSION)
    award_xp(user_id, "discipline", XP_POMODORO_SESSION)
    from services.streak_service import record_activity
    record_activity(user_id)
    return check_and_unlock_badges(user_id, trigger="pomodoro_complete")


def abandon_session(session_id: int) -> None:
    _repo.abandon_session(session_id)


def get_today_summary(user_id: int) -> dict:
    sessions = _repo.get_completed_today(user_id)
    total_min = sum(s.work_minutes for s in sessions)
    return {
        "sessions": len(sessions),
        "total_minutes": total_min,
        "total_display": minutes_to_hm(total_min),
    }


def get_week_summary(user_id: int) -> dict:
    start = fmt_date(start_of_week())
    end = fmt_date(end_of_week())
    minutes = _repo.total_work_minutes(user_id, start, end)
    sessions = _repo.total_sessions(user_id, start, end)
    return {"sessions": sessions, "minutes": minutes, "display": minutes_to_hm(minutes)}


def get_history(user_id: int, limit: int = 50) -> list[PomodoroSession]:
    return _repo.get_for_user(user_id, limit)


def get_daily_chart_data(user_id: int, start: str, end: str) -> list[dict]:
    return _repo.daily_minutes(user_id, start, end)


def get_subject_breakdown(user_id: int, start: str, end: str) -> list[dict]:
    return _repo.by_subject(user_id, start, end)
