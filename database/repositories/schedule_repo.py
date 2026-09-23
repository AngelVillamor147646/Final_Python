"""Schedule repository."""
from __future__ import annotations
import sqlite3
from typing import Optional
from database.repositories.base import BaseRepository
from models import Schedule


class ScheduleRepository(BaseRepository[Schedule]):
    TABLE = "schedules"

    def _row_to_model(self, row: sqlite3.Row) -> Schedule:
        return Schedule(
            id=row["id"], user_id=row["user_id"], title=row["title"],
            day_of_week=row["day_of_week"], start_time=row["start_time"],
            end_time=row["end_time"], subject_id=row["subject_id"],
            room=row["room"] or "", instructor=row["instructor"] or "",
            color=row["color"] or "#7C4DFF",
            reminder_minutes=row["reminder_minutes"] or 15,
            is_active=bool(row["is_active"]),
            created_at=row["created_at"],
        )

    def create(
        self, user_id: int, title: str, day_of_week: int,
        start_time: str, end_time: str, subject_id: Optional[int] = None,
        room: str = "", instructor: str = "", color: str = "#7C4DFF",
        reminder_minutes: int = 15,
    ) -> Schedule:
        row_id = self._insert({
            "user_id": user_id, "title": title, "day_of_week": day_of_week,
            "start_time": start_time, "end_time": end_time,
            "subject_id": subject_id, "room": room,
            "instructor": instructor, "color": color,
            "reminder_minutes": reminder_minutes,
        })
        return self.get_by_id(row_id)  # type: ignore[return-value]

    def update(
        self, schedule_id: int, title: str, day_of_week: int,
        start_time: str, end_time: str, subject_id: Optional[int],
        room: str, instructor: str, color: str, reminder_minutes: int,
    ) -> bool:
        cur = self._execute(
            """UPDATE schedules SET title=?, day_of_week=?, start_time=?,
               end_time=?, subject_id=?, room=?, instructor=?,
               color=?, reminder_minutes=? WHERE id=?""",
            (title, day_of_week, start_time, end_time, subject_id,
             room, instructor, color, reminder_minutes, schedule_id),
        )
        self._commit()
        return cur.rowcount > 0

    def get_for_user(self, user_id: int, active_only: bool = True) -> list[Schedule]:
        sql = "SELECT * FROM schedules WHERE user_id=?"
        params: tuple = (user_id,)
        if active_only:
            sql += " AND is_active=1"
        sql += " ORDER BY day_of_week, start_time"
        rows = self._fetchall(sql, params)
        return self._rows_to_models(rows)

    def get_for_day(self, user_id: int, day_of_week: int) -> list[Schedule]:
        rows = self._fetchall(
            """SELECT * FROM schedules
               WHERE user_id=? AND day_of_week=? AND is_active=1
               ORDER BY start_time""",
            (user_id, day_of_week),
        )
        return self._rows_to_models(rows)

    def detect_conflicts(
        self, user_id: int, day_of_week: int,
        start_time: str, end_time: str,
        exclude_id: Optional[int] = None,
    ) -> list[Schedule]:
        """Return existing schedules that overlap the given time range."""
        sql = """
            SELECT * FROM schedules
            WHERE user_id=? AND day_of_week=? AND is_active=1
            AND start_time < ? AND end_time > ?
        """
        params: list = [user_id, day_of_week, end_time, start_time]
        if exclude_id is not None:
            sql += " AND id != ?"
            params.append(exclude_id)
        rows = self._fetchall(sql, tuple(params))
        return self._rows_to_models(rows)

    def toggle_active(self, schedule_id: int) -> bool:
        cur = self._execute(
            "UPDATE schedules SET is_active = NOT is_active WHERE id=?",
            (schedule_id,),
        )
        self._commit()
        return cur.rowcount > 0

    def count_for_user(self, user_id: int) -> int:
        return self.count("user_id=?", (user_id,))
