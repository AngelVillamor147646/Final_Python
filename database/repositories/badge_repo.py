"""Badge repository — definition lookups and user unlock tracking."""
from __future__ import annotations
import sqlite3
from typing import Optional
from database.repositories.base import BaseRepository
from models import Badge


class BadgeRepository(BaseRepository[Badge]):
    TABLE = "badges"

    def _row_to_model(self, row: sqlite3.Row) -> Badge:
        return Badge(
            id=row["id"], slug=row["slug"], name=row["name"],
            description=row["description"] or "",
            icon=row["icon"] or "trophy",
            category=row["category"] or "general",
            xp_reward=row["xp_reward"] or 50,
            is_hidden=bool(row["is_hidden"]),
            unlocked_at=row.keys() and "unlocked_at" in row.keys() and row["unlocked_at"] or None,
            is_unlocked=bool(row.keys() and "unlocked_at" in row.keys() and row["unlocked_at"]),
        )

    def get_all_with_status(self, user_id: int) -> list[Badge]:
        """Return all badges joined with user unlock status."""
        rows = self._fetchall(
            """SELECT b.*, ub.unlocked_at
               FROM badges b
               LEFT JOIN user_badges ub ON ub.badge_id=b.id AND ub.user_id=?
               ORDER BY b.category, b.name""",
            (user_id,),
        )
        result = []
        for row in rows:
            b = Badge(
                id=row["id"], slug=row["slug"], name=row["name"],
                description=row["description"] or "",
                icon=row["icon"] or "trophy",
                category=row["category"] or "general",
                xp_reward=row["xp_reward"] or 50,
                is_hidden=bool(row["is_hidden"]),
                unlocked_at=row["unlocked_at"],
                is_unlocked=row["unlocked_at"] is not None,
            )
            result.append(b)
        return result

    def is_unlocked(self, user_id: int, badge_slug: str) -> bool:
        row = self._fetchone(
            """SELECT ub.id FROM user_badges ub
               JOIN badges b ON b.id=ub.badge_id
               WHERE ub.user_id=? AND b.slug=?""",
            (user_id, badge_slug),
        )
        return row is not None

    def unlock(self, user_id: int, badge_slug: str) -> Optional[Badge]:
        """Unlock badge for user; returns the Badge if newly unlocked, else None."""
        if self.is_unlocked(user_id, badge_slug):
            return None
        badge = self._fetchone("SELECT * FROM badges WHERE slug=?", (badge_slug,))
        if not badge:
            return None
        self._execute(
            "INSERT OR IGNORE INTO user_badges (user_id, badge_id) VALUES (?, ?)",
            (user_id, badge["id"]),
        )
        self._commit()
        return Badge(
            id=badge["id"], slug=badge["slug"], name=badge["name"],
            description=badge["description"] or "",
            icon=badge["icon"] or "trophy",
            category=badge["category"] or "general",
            xp_reward=badge["xp_reward"] or 50,
            is_unlocked=True,
        )

    def get_unlocked_for_user(self, user_id: int) -> list[Badge]:
        rows = self._fetchall(
            """SELECT b.*, ub.unlocked_at FROM badges b
               JOIN user_badges ub ON ub.badge_id=b.id
               WHERE ub.user_id=? ORDER BY ub.unlocked_at DESC""",
            (user_id,),
        )
        result = []
        for row in rows:
            b = Badge(
                id=row["id"], slug=row["slug"], name=row["name"],
                description=row["description"] or "",
                icon=row["icon"] or "trophy",
                category=row["category"] or "general",
                xp_reward=row["xp_reward"] or 50,
                is_unlocked=True,
                unlocked_at=row["unlocked_at"],
            )
            result.append(b)
        return result

    def count_unlocked(self, user_id: int) -> int:
        row = self._fetchone(
            "SELECT COUNT(*) AS n FROM user_badges WHERE user_id=?", (user_id,)
        )
        return row["n"] if row else 0

    def get_recent(self, user_id: int, limit: int = 5) -> list[Badge]:
        rows = self._fetchall(
            """SELECT b.*, ub.unlocked_at FROM badges b
               JOIN user_badges ub ON ub.badge_id=b.id
               WHERE ub.user_id=? ORDER BY ub.unlocked_at DESC LIMIT ?""",
            (user_id, limit),
        )
        result = []
        for row in rows:
            result.append(Badge(
                id=row["id"], slug=row["slug"], name=row["name"],
                description=row["description"] or "",
                icon=row["icon"] or "trophy",
                category=row["category"] or "general",
                xp_reward=row["xp_reward"] or 50,
                is_unlocked=True,
                unlocked_at=row["unlocked_at"],
            ))
        return result
