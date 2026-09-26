"""Schedule service — weekly timetable management with conflict detection."""
from __future__ import annotations
from typing import Optional
from database.repositories import ScheduleRepository, SubjectRepository
from models import Schedule
from utils.logger import get_logger
from utils.validation import validate_required, validate_time_order

log = get_logger(__name__)
_repo = ScheduleRepository()
_subj_repo = SubjectRepository()

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


import json

def get_weekly_schedule(user_id: int) -> dict[int, list[Schedule]]:
    """Return dict keyed by day_of_week (0=Mon) → list of schedules."""
    all_schedules = _repo.get_for_user(user_id)
    result: dict[int, list[Schedule]] = {i: [] for i in range(7)}
    for s in all_schedules:
        try:
            days = json.loads(s.days)
            for d in days:
                result[int(d)].append(s)
        except:
            pass
    return result


def get_day_schedule(user_id: int, day_of_week: int) -> list[Schedule]:
    return _repo.get_for_day(user_id, day_of_week)


def create_schedule(user_id: int, title: str, days: list[int],
                    start_time: str, end_time: str, subject_id=None,
                    room="", instructor="", color="#7C4DFF", notes="",
                    reminder_minutes=15) -> tuple[bool, str, Optional[Schedule]]:
    ok, err = validate_required(title, "Title")
    if not ok:
        return False, err, None
    ok, err = validate_time_order(start_time, end_time)
    if not ok:
        return False, err, None
    if not days:
        return False, "Please select at least one day.", None

    # Check conflicts for all selected days
    for d in days:
        conflicts = _repo.detect_conflicts(user_id, d, start_time, end_time)
        if conflicts:
            names = ", ".join(c.title for c in conflicts)
            return False, f"Time conflicts on {DAY_NAMES[d]} with: {names}", None
    
    try:
        s = _repo.create(user_id, title.strip(), json.dumps(days), start_time,
                         end_time, subject_id, room, instructor, color, notes, reminder_minutes)
        from services.notification_service import schedule_class_reminder
        schedule_class_reminder(s)
        return True, "", s
    except Exception as exc:
        log.error("create_schedule: %s", exc)
        return False, "Failed to save schedule.", None


def update_schedule(schedule_id: int, user_id: int, title: str, days: list[int],
                    start_time: str, end_time: str, subject_id=None,
                    room="", instructor="", color="#7C4DFF", notes="",
                    reminder_minutes=15) -> tuple[bool, str]:
    ok, err = validate_required(title, "Title")
    if not ok:
        return False, err
    ok, err = validate_time_order(start_time, end_time)
    if not ok:
        return False, err
    if not days:
        return False, "Please select at least one day."

    for d in days:
        conflicts = _repo.detect_conflicts(user_id=user_id, day_of_week=d,
                                           start_time=start_time, end_time=end_time,
                                           exclude_id=schedule_id)
        if conflicts:
            names = ", ".join(c.title for c in conflicts)
            return False, f"Time conflicts on {DAY_NAMES[d]} with: {names}"

    try:
        _repo.update(schedule_id, title.strip(), json.dumps(days), start_time,
                     end_time, subject_id, room, instructor, color, notes, reminder_minutes)
        s = _repo.get_by_id(schedule_id)
        if s:
            from services.notification_service import schedule_class_reminder
            schedule_class_reminder(s)
        return True, ""
    except Exception as exc:
        log.error("update_schedule: %s", exc)
        return False, "Failed to update schedule."


def delete_schedule(schedule_id: int) -> bool:
    return _repo.delete_by_id(schedule_id)


def get_subjects(user_id: int):
    return _subj_repo.get_for_user(user_id)


def toggle_active(schedule_id: int) -> bool:
    return _repo.toggle_active(schedule_id)


def get_today_classes(user_id: int) -> list[Schedule]:
    from datetime import date
    dow = date.today().weekday()
    return _repo.get_for_day(user_id, dow)
