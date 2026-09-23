"""Task service — full business logic for task management."""
from __future__ import annotations
from datetime import date
from typing import Optional
from database.repositories import TaskRepository, SubjectRepository
from models import Task
from utils.logger import get_logger
from utils.validation import validate_required, validate_name
from utils import fmt_date

log = get_logger(__name__)
_repo = TaskRepository()
_subj_repo = SubjectRepository()


def get_user_tasks(user_id: int, status=None, subject_id=None,
                   priority=None, search="", order_by="deadline ASC, created_at DESC") -> list[Task]:
    return _repo.get_for_user(user_id, status, subject_id, priority, search, order_by)


def get_today_tasks(user_id: int) -> list[Task]:
    return _repo.get_due_today(user_id)


def get_upcoming_tasks(user_id: int, days: int = 7) -> list[Task]:
    return _repo.get_upcoming(user_id, days)


def get_overdue_tasks(user_id: int) -> list[Task]:
    return _repo.get_overdue(user_id)


def create_task(user_id: int, title: str, subject_id=None, description="",
                priority="medium", label_color="#7C4DFF", deadline=None,
                reminder_at=None, is_recurring=False, recur_rule=None) -> tuple[bool, str, Optional[Task]]:
    ok, err = validate_name(title, "Title")
    if not ok:
        return False, err, None
    try:
        task = _repo.create(user_id, title.strip(), subject_id, description,
                            priority, label_color, deadline, reminder_at,
                            is_recurring, recur_rule)
        _maybe_schedule_notification(task)
        return True, "", task
    except Exception as exc:
        log.error("create_task failed: %s", exc)
        return False, "Failed to save task.", None


def update_task(task_id: int, title: str, subject_id=None, description="",
                priority="medium", label_color="#7C4DFF", deadline=None,
                reminder_at=None, is_recurring=False, recur_rule=None) -> tuple[bool, str]:
    ok, err = validate_name(title, "Title")
    if not ok:
        return False, err
    try:
        _repo.update(task_id, title.strip(), subject_id, description, priority,
                     label_color, deadline, reminder_at, is_recurring, recur_rule)
        task = _repo.get_by_id(task_id)
        if task:
            _maybe_schedule_notification(task)
        return True, ""
    except Exception as exc:
        log.error("update_task failed: %s", exc)
        return False, "Failed to update task."


def complete_task(task_id: int, user_id: int) -> tuple[bool, list[str]]:
    """Mark task done; trigger gamification; return (ok, [badge_slugs_unlocked])."""
    ok = _repo.mark_done(task_id)
    if not ok:
        return False, []
    badges = _check_task_badges(user_id)
    _award_task_xp(user_id)
    return True, badges


def delete_task(task_id: int) -> bool:
    return _repo.delete_by_id(task_id)


def get_task(task_id: int) -> Optional[Task]:
    return _repo.get_by_id(task_id)


def get_subjects(user_id: int):
    return _subj_repo.get_for_user(user_id)


def create_subject(user_id: int, name: str, color="#7C4DFF",
                   instructor="", room="") -> tuple[bool, str]:
    ok, err = validate_name(name, "Subject name")
    if not ok:
        return False, err
    _subj_repo.create(user_id, name.strip(), color, instructor, room)
    return True, ""


# ── private helpers ────────────────────────────────────────────────────────

def _maybe_schedule_notification(task: Task) -> None:
    if task.reminder_at:
        try:
            from services.notification_service import schedule_task_reminder
            schedule_task_reminder(task)
        except Exception as exc:
            log.warning("Could not schedule notification: %s", exc)


def _check_task_badges(user_id: int) -> list[str]:
    from services.gamification_service import check_and_unlock_badges
    return check_and_unlock_badges(user_id, trigger="task_complete")


def _award_task_xp(user_id: int) -> None:
    from services.gamification_service import award_xp
    from config import XP_TASK_COMPLETE
    award_xp(user_id, "time_management", XP_TASK_COMPLETE)
    award_xp(user_id, "productivity", XP_TASK_COMPLETE)
