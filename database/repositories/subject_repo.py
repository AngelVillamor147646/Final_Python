"""Subject repository."""
from __future__ import annotations
import sqlite3
from typing import Optional
from database.repositories.base import BaseRepository
from models import Subject


class SubjectRepository(BaseRepository[Subject]):
    TABLE = "subjects"

    def _row_to_model(self, row: sqlite3.Row) -> Subject:
        return Subject(
            id=row["id"], user_id=row["user_id"], name=row["name"],
            color=row["color"], instructor=row["instructor"] or "",
            room=row["room"] or "", created_at=row["created_at"],
        )

    def create(self, user_id: int, name: str, color: str = "#7C4DFF",
               instructor: str = "", room: str = "") -> Subject:
        row_id = self._insert({
            "user_id": user_id, "name": name, "color": color,
            "instructor": instructor, "room": room,
        })
        return self.get_by_id(row_id)  # type: ignore[return-value]

    def get_for_user(self, user_id: int) -> list[Subject]:
        rows = self._fetchall(
            "SELECT * FROM subjects WHERE user_id=? ORDER BY name", (user_id,)
        )
        return self._rows_to_models(rows)

    def update(self, subject_id: int, name: str, color: str,
               instructor: str, room: str) -> bool:
        cur = self._execute(
            "UPDATE subjects SET name=?, color=?, instructor=?, room=? WHERE id=?",
            (name, color, instructor, room, subject_id),
        )
        self._commit()
        return cur.rowcount > 0

    def get_by_name(self, user_id: int, name: str) -> Optional[Subject]:
        row = self._fetchone(
            "SELECT * FROM subjects WHERE user_id=? AND name=? COLLATE NOCASE",
            (user_id, name),
        )
        return self._row_to_model(row) if row else None
