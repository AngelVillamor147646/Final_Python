"""Habit service — manage user-defined skills, streaks, and reminders."""
from __future__ import annotations
from typing import Optional
from database.connection import execute, commit, fetchall, fetchone
from models import UserSkill
from utils.logger import get_logger
from datetime import date, datetime, timedelta

log = get_logger(__name__)

def _row_to_skill(row) -> UserSkill:
    return UserSkill(
        id=row["id"], user_id=row["user_id"], skill_name=row["skill_name"],
        reminder_time=row["reminder_time"], streak=row["streak"],
        longest_streak=row["longest_streak"], last_completed=row["last_completed"],
        notification_enabled=bool(row["notification_enabled"]), updated_at=row["updated_at"]
    )

def get_user_habits(user_id: int) -> list[UserSkill]:
    rows = fetchall("SELECT * FROM user_skills WHERE user_id=?", (user_id,))
    return [_row_to_skill(r) for r in rows]

def create_habit(user_id: int, name: str, reminder_time: str = "", notification_enabled: bool = False) -> tuple[bool, str, Optional[UserSkill]]:
    if not name.strip():
        return False, "Name cannot be empty.", None
    try:
        cur = execute(
            """INSERT INTO user_skills (user_id, skill_name, reminder_time, notification_enabled) 
               VALUES (?, ?, ?, ?)""",
            (user_id, name.strip(), reminder_time, 1 if notification_enabled else 0)
        )
        commit()
        row = fetchone("SELECT * FROM user_skills WHERE id=?", (cur.lastrowid,))
        return True, "", _row_to_skill(row)
    except Exception as exc:
        log.error("create_habit failed: %s", exc)
        return False, "Failed to create habit (maybe it already exists?).", None

def delete_habit(habit_id: int) -> bool:
    cur = execute("DELETE FROM user_skills WHERE id=?", (habit_id,))
    commit()
    return cur.rowcount > 0

def complete_habit(habit_id: int) -> tuple[bool, str]:
    row = fetchone("SELECT * FROM user_skills WHERE id=?", (habit_id,))
    if not row:
        return False, "Habit not found."
    
    habit = _row_to_skill(row)
    today = date.today().isoformat()
    
    # If already completed today, do nothing
    if habit.last_completed and habit.last_completed.startswith(today):
        return False, "Already completed today."

    # Check streak logic
    new_streak = habit.streak + 1
    if habit.last_completed:
        last_date = datetime.fromisoformat(habit.last_completed[:10]).date()
        if (date.today() - last_date).days > 1:
            new_streak = 1 # streak broken
            
    longest = max(habit.longest_streak, new_streak)

    execute(
        """UPDATE user_skills 
           SET streak=?, longest_streak=?, last_completed=?, updated_at=datetime('now','localtime') 
           WHERE id=?""",
        (new_streak, longest, datetime.now().isoformat(), habit_id)
    )
    commit()
    
    return True, f"Streak is now {new_streak}!"
