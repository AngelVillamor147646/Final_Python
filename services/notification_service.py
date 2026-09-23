"""Notification service — Plyer wrapper + persistent DB scheduler."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from utils.logger import get_logger
from models import Task, Schedule

log = get_logger(__name__)


def _send_now(title: str, message: str, ticker: str = "") -> None:
    """Fire a local notification via Plyer (best-effort)."""
    try:
        from plyer import notification
        from config import NOTIFICATION_APP_NAME, NOTIFICATION_ICON
        notification.notify(
            title=title,
            message=message,
            app_name=NOTIFICATION_APP_NAME,
            app_icon=NOTIFICATION_ICON if __import__("os").path.exists(NOTIFICATION_ICON) else "",
            timeout=8,
        )
    except Exception as exc:
        log.warning("Plyer notification failed: %s", exc)


def send_notification(title: str, body: str) -> None:
    _send_now(title, body)


def schedule_task_reminder(task: Task) -> None:
    """Persist a task reminder notification to the DB."""
    if not task.reminder_at:
        return
    from database.repositories import NotificationRepository
    from services.auth_service import get_active_user
    user = get_active_user()
    if not user:
        return
    repo = NotificationRepository()
    repo.delete_for_ref(task.id, "task_reminder")
    repo.schedule(
        user_id=user.id, notif_type="task_reminder",
        title=f"📌 {task.title}",
        body=f"Reminder: '{task.title}' is due soon.",
        scheduled_at=task.reminder_at, ref_id=task.id,
    )


def schedule_class_reminder(schedule: Schedule) -> None:
    """Schedule a class start reminder (approximate, using next occurrence)."""
    from database.repositories import NotificationRepository
    from services.auth_service import get_active_user
    from utils.date_utils import today, week_dates
    user = get_active_user()
    if not user:
        return
    dates = week_dates()
    target_date = dates[schedule.day_of_week]
    sched_dt = datetime.combine(target_date, datetime.strptime(schedule.start_time, "%H:%M").time())
    from datetime import timedelta
    remind_dt = sched_dt - timedelta(minutes=schedule.reminder_minutes)
    repo = NotificationRepository()
    repo.delete_for_ref(schedule.id, "class_reminder")
    repo.schedule(
        user_id=user.id, notif_type="class_reminder",
        title=f"🏫 {schedule.title}",
        body=f"Class '{schedule.title}' starts in {schedule.reminder_minutes} min.",
        scheduled_at=remind_dt.strftime("%Y-%m-%d %H:%M"),
        ref_id=schedule.id,
    )


def send_pomodoro_notification(kind: str = "work") -> None:
    if kind == "work":
        _send_now("🍅 Pomodoro Complete!", "Great focus! Time for a break.")
    elif kind == "break":
        _send_now("⏰ Break Over!", "Ready for another session?")
    elif kind == "long_break":
        _send_now("🎉 Long Break!", "You've earned a long rest. Relax!")


def dispatch_pending(user_id: int) -> int:
    """
    Check DB for pending notifications due now; fire them.
    Returns count dispatched.
    """
    from database.repositories import NotificationRepository
    repo = NotificationRepository()
    pending = repo.get_pending(user_id)
    for notif in pending:
        _send_now(notif.title, notif.body)
        repo.mark_sent(notif.id)
    if pending:
        log.info("Dispatched %d notification(s).", len(pending))
    return len(pending)
