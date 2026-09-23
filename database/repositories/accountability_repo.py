"""Accountability history repository."""
from __future__ import annotations
import sqlite3
from database.repositories.base import BaseRepository
from models import AccountabilityEntry
from utils.helpers import safe_json_loads


class AccountabilityRepository(BaseRepository[AccountabilityEntry]):
    TABLE = "accountability_history"

    def _row_to_model(self, row: sqlite3.Row) -> AccountabilityEntry:
        return AccountabilityEntry(
            id=row["id"], user_id=row["user_id"],
            date=row["date"], score=row["score"] or 0.0,
            breakdown_json=row["breakdown_json"] or "{}",
            created_at=row["created_at"],
        )

    def upsert(self, user_id: int, date_str: str, score: float, breakdown: dict) -> None:
        import json
        self._execute(
            """INSERT INTO accountability_history (user_id, date, score, breakdown_json)
               VALUES (?, ?, ?, ?)
               ON CONFLICT(user_id, date) DO UPDATE SET
               score=excluded.score, breakdown_json=excluded.breakdown_json,
               created_at=datetime('now','localtime')""",
            (user_id, date_str, round(score, 2), json.dumps(breakdown)),
        )
        self._commit()

    def get_history(self, user_id: int, days: int = 30) -> list[AccountabilityEntry]:
        rows = self._fetchall(
            """SELECT * FROM accountability_history
               WHERE user_id=? AND date >= date('now', ?||' days')
               ORDER BY date DESC""",
            (user_id, f"-{days}"),
        )
        return self._rows_to_models(rows)

    def get_today(self, user_id: int) -> AccountabilityEntry | None:
        row = self._fetchone(
            "SELECT * FROM accountability_history WHERE user_id=? AND date=date('now')",
            (user_id,),
        )
        return self._row_to_model(row) if row else None

    def average_score(self, user_id: int, days: int = 7) -> float:
        row = self._fetchone(
            """SELECT COALESCE(AVG(score), 0) AS avg_score
               FROM accountability_history
               WHERE user_id=? AND date >= date('now', ?||' days')""",
            (user_id, f"-{days}"),
        )
        return row["avg_score"] if row else 0.0

    def weekly_average(self, user_id: int) -> float:
        return self.average_score(user_id, days=7)

    def chart_data(self, user_id: int, days: int = 30) -> list[dict]:
        rows = self._fetchall(
            """SELECT date, score FROM accountability_history
               WHERE user_id=? AND date >= date('now', ?||' days')
               ORDER BY date ASC""",
            (user_id, f"-{days}"),
        )
        return [{"date": r["date"], "score": r["score"]} for r in rows]
