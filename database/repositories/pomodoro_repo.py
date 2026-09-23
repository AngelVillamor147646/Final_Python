"""Pomodoro session repository."""
from __future__ import annotations
import sqlite3
from typing import Optional
from database.repositories.base import BaseRepository
from models import PomodoroSession


class PomodoroRepository(BaseRepository[PomodoroSession]):
    TABLE = "pomodoro_sessions"

    def _row_to_model(self, row: sqlite3.Row) -> PomodoroSession:
        return PomodoroSession(
            id=row["id"], user_id=row["user_id"],
            started_at=row["started_at"],
            work_minutes=row["work_minutes"],
            break_minutes=row["break_minutes"],
            subject_id=row["subject_id"],
            task_id=row["task_id"],
            ended_at=row["ended_at"],
            completed=bool(row["completed"]),
            interruptions=row["interruptions"] or 0,
            notes=row["notes"] or "",
        )

    def create_session(
        self, user_id: int, work_minutes: int = 25, break_minutes: int = 5,
        subject_id: Optional[int] = None, task_id: Optional[int] = None,
    ) -> PomodoroSession:
        row_id = self._insert({
            "user_id": user_id, "work_minutes": work_minutes,
            "break_minutes": break_minutes, "subject_id": subject_id,
            "task_id": task_id,
        })
        return self.get_by_id(row_id)  # type: ignore[return-value]

    def complete_session(self, session_id: int, interruptions: int = 0, notes: str = "") -> bool:
        cur = self._execute(
            """UPDATE pomodoro_sessions SET completed=1,
               ended_at=datetime('now','localtime'),
               interruptions=?, notes=? WHERE id=?""",
            (interruptions, notes, session_id),
        )
        self._commit()
        return cur.rowcount > 0

    def abandon_session(self, session_id: int) -> bool:
        cur = self._execute(
            """UPDATE pomodoro_sessions SET completed=0,
               ended_at=datetime('now','localtime') WHERE id=?""",
            (session_id,),
        )
        self._commit()
        return cur.rowcount > 0

    def get_for_user(self, user_id: int, limit: int = 50) -> list[PomodoroSession]:
        rows = self._fetchall(
            "SELECT * FROM pomodoro_sessions WHERE user_id=? ORDER BY started_at DESC LIMIT ?",
            (user_id, limit),
        )
        return self._rows_to_models(rows)

    def get_completed_today(self, user_id: int) -> list[PomodoroSession]:
        rows = self._fetchall(
            """SELECT * FROM pomodoro_sessions
               WHERE user_id=? AND completed=1
               AND date(started_at)=date('now')
               ORDER BY started_at DESC""",
            (user_id,),
        )
        return self._rows_to_models(rows)

    def total_work_minutes(self, user_id: int, start: str, end: str) -> int:
        """Sum work_minutes for completed sessions between dates."""
        row = self._fetchone(
            """SELECT COALESCE(SUM(work_minutes), 0) AS total
               FROM pomodoro_sessions
               WHERE user_id=? AND completed=1
               AND date(started_at) BETWEEN ? AND ?""",
            (user_id, start, end),
        )
        return row["total"] if row else 0

    def total_sessions(self, user_id: int, start: str, end: str) -> int:
        row = self._fetchone(
            """SELECT COUNT(*) AS n FROM pomodoro_sessions
               WHERE user_id=? AND completed=1
               AND date(started_at) BETWEEN ? AND ?""",
            (user_id, start, end),
        )
        return row["n"] if row else 0

    def daily_minutes(self, user_id: int, start: str, end: str) -> list[dict]:
        """Return list of {date, minutes} for chart rendering."""
        rows = self._fetchall(
            """SELECT date(started_at) AS day, SUM(work_minutes) AS minutes
               FROM pomodoro_sessions
               WHERE user_id=? AND completed=1
               AND date(started_at) BETWEEN ? AND ?
               GROUP BY day ORDER BY day""",
            (user_id, start, end),
        )
        return [{"date": r["day"], "minutes": r["minutes"]} for r in rows]

    def by_subject(self, user_id: int, start: str, end: str) -> list[dict]:
        rows = self._fetchall(
            """SELECT s.name AS subject, SUM(p.work_minutes) AS minutes
               FROM pomodoro_sessions p
               LEFT JOIN subjects s ON p.subject_id = s.id
               WHERE p.user_id=? AND p.completed=1
               AND date(p.started_at) BETWEEN ? AND ?
               GROUP BY p.subject_id""",
            (user_id, start, end),
        )
        return [{"subject": r["subject"] or "Unassigned", "minutes": r["minutes"]} for r in rows]
