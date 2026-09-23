"""Streak repository — daily/weekly tracking and analytics."""
from __future__ import annotations
import sqlite3
from datetime import date, timedelta
from database.repositories.base import BaseRepository
from models import StreakEntry


class StreakRepository(BaseRepository[StreakEntry]):
    TABLE = "streaks"

    def _row_to_model(self, row: sqlite3.Row) -> StreakEntry:
        return StreakEntry(
            id=row["id"], user_id=row["user_id"],
            date=row["date"], streak_type=row["streak_type"],
        )

    def record_today(self, user_id: int, streak_type: str = "daily") -> bool:
        """Record a streak entry for today. Returns True if new entry created."""
        today_str = date.today().isoformat()
        cur = self._execute(
            "INSERT OR IGNORE INTO streaks (user_id, date, streak_type) VALUES (?, ?, ?)",
            (user_id, today_str, streak_type),
        )
        self._commit()
        return cur.rowcount > 0

    def has_entry(self, user_id: int, date_str: str, streak_type: str = "daily") -> bool:
        row = self._fetchone(
            "SELECT id FROM streaks WHERE user_id=? AND date=? AND streak_type=?",
            (user_id, date_str, streak_type),
        )
        return row is not None

    def current_streak(self, user_id: int, streak_type: str = "daily") -> int:
        """Return the current consecutive streak count ending today (or yesterday)."""
        rows = self._fetchall(
            """SELECT date FROM streaks
               WHERE user_id=? AND streak_type=?
               ORDER BY date DESC""",
            (user_id, streak_type),
        )
        if not rows:
            return 0

        dates = {row["date"] for row in rows}
        count = 0
        check = date.today()
        # Allow one day grace: check today first, then yesterday
        if check.isoformat() not in dates:
            check = check - timedelta(days=1)
        while check.isoformat() in dates:
            count += 1
            check = check - timedelta(days=1)
        return count

    def longest_streak(self, user_id: int, streak_type: str = "daily") -> int:
        """Return the longest ever consecutive streak."""
        rows = self._fetchall(
            """SELECT date FROM streaks
               WHERE user_id=? AND streak_type=?
               ORDER BY date ASC""",
            (user_id, streak_type),
        )
        if not rows:
            return 0

        dates = [date.fromisoformat(r["date"]) for r in rows]
        max_streak = current = 1
        for i in range(1, len(dates)):
            if (dates[i] - dates[i - 1]).days == 1:
                current += 1
                max_streak = max(max_streak, current)
            else:
                current = 1
        return max_streak

    def get_calendar_data(self, user_id: int, year: int, month: int) -> list[str]:
        """Return list of date strings (YYYY-MM-DD) active in the given month."""
        rows = self._fetchall(
            """SELECT date FROM streaks
               WHERE user_id=? AND streak_type='daily'
               AND date LIKE ?""",
            (user_id, f"{year}-{month:02d}-%"),
        )
        return [r["date"] for r in rows]

    def get_all_dates(self, user_id: int, streak_type: str = "daily") -> list[str]:
        rows = self._fetchall(
            """SELECT date FROM streaks WHERE user_id=? AND streak_type=?
               ORDER BY date DESC""",
            (user_id, streak_type),
        )
        return [r["date"] for r in rows]

    def total_active_days(self, user_id: int) -> int:
        row = self._fetchone(
            "SELECT COUNT(DISTINCT date) AS n FROM streaks WHERE user_id=? AND streak_type='daily'",
            (user_id,),
        )
        return row["n"] if row else 0

    def missed_yesterday(self, user_id: int) -> bool:
        """Return True if yesterday has no streak entry."""
        yesterday = (date.today() - timedelta(days=1)).isoformat()
        return not self.has_entry(user_id, yesterday)
