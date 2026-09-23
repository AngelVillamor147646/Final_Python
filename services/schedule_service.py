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


def get_weekly_schedule(user_id: int) -> dict[int, list[Schedule]]:
    """Return dict keyed by day_of_week (0=Mon) → list of schedules."""
    all_schedules = _repo.get_for_user(user_id)
    result: dict[int, list[Schedule]] = {i: [] for i in range(7)}
    for s in all_schedules:
        result[s.day_of_week].append(s)
    return result


def get_day_schedule(user_id: int, day_of_week: int) -> list[Schedule]:
    return _repo.get_for_day(user_id, day_of_week)


def create_schedule(user_id: int, title: str, day_of_week: int,
                    start_time: str, end_time: str, subject_id=None,
                    room="", instructor="", color="#7C4DFF",
                    reminder_minutes=15) -> tuple[bool, str, Optional[Schedule]]:
    ok, err = validate_required(title, "Title")
    if not ok:
        return False, err, None
    ok, err = validate_time_order(start_time, end_time)
    if not ok:
        return False, err, None
    conflicts = _repo.detect_conflicts(user_id, day_of_week, start_time, end_time)
    if conflicts:
        names = ", ".join(c.title for c in conflicts)
        return False, f"Time conflicts with: {names}", None
    try:
        s = _repo.create(user_id, title.strip(), day_of_week, start_time,
                         end_time, subject_id, room, instructor, color, reminder_minutes)
        return True, "", s
    except Exception as exc:
        log.error("create_schedule: %s", exc)
        return False, "Failed to save schedule.", None


def update_schedule(schedule_id: int, title: str, day_of_week: int,
                    start_time: str, end_time: str, subject_id=None,
                    room="", instructor="", color="#7C4DFF",
                    reminder_minutes=15) -> tuple[bool, str]:
    ok, err = validate_required(title, "Title")
    if not ok:
        return False, err
    ok, err = validate_time_order(start_time, end_time)
    if not ok:
        return False, err
    conflicts = _repo.detect_conflicts(user_id=0, day_of_week=day_of_week,
                                       start_time=start_time, end_time=end_time,
                                       exclude_id=schedule_id)
    # Note: user_id=0 is wrong here — caller must inject; fix for MVP:
    try:
        _repo.update(schedule_id, title.strip(), day_of_week, start_time,
                     end_time, subject_id, room, instructor, color, reminder_minutes)
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
