"""Skill repository — definitions and per-user XP/level tracking."""
from __future__ import annotations
import sqlite3
from database.repositories.base import BaseRepository
from models import Skill


class SkillRepository(BaseRepository[Skill]):
    TABLE = "skills"

    def _row_to_model(self, row: sqlite3.Row) -> Skill:
        return Skill(
            id=row["id"], slug=row["slug"], name=row["name"],
            description=row["description"] or "",
            icon=row["icon"] or "star",
            max_level=row["max_level"], xp_per_level=row["xp_per_level"],
        )

    def get_all_with_progress(self, user_id: int) -> list[Skill]:
        rows = self._fetchall(
            """SELECT s.*, us.current_level, us.current_xp, us.total_xp
               FROM skills s
               LEFT JOIN user_skills us ON us.skill_id=s.id AND us.user_id=?
               ORDER BY s.name""",
            (user_id,),
        )
        result = []
        for row in rows:
            skill = Skill(
                id=row["id"], slug=row["slug"], name=row["name"],
                description=row["description"] or "",
                icon=row["icon"] or "star",
                max_level=row["max_level"], xp_per_level=row["xp_per_level"],
                current_level=row["current_level"] or 0,
                current_xp=row["current_xp"] or 0,
                total_xp=row["total_xp"] or 0,
            )
            result.append(skill)
        return result

    def _ensure_user_skill(self, user_id: int, skill_id: int) -> None:
        self._execute(
            "INSERT OR IGNORE INTO user_skills (user_id, skill_id) VALUES (?, ?)",
            (user_id, skill_id),
        )
        self._commit()

    def add_xp(self, user_id: int, skill_slug: str, xp: int) -> dict:
        """
        Add *xp* to the named skill. Returns a dict with keys:
        ``leveled_up`` (bool), ``new_level`` (int), ``new_xp`` (int).
        """
        skill_row = self._fetchone("SELECT * FROM skills WHERE slug=?", (skill_slug,))
        if not skill_row:
            return {"leveled_up": False, "new_level": 0, "new_xp": 0}

        skill_id = skill_row["id"]
        xp_per_level = skill_row["xp_per_level"]
        max_level = skill_row["max_level"]

        self._ensure_user_skill(user_id, skill_id)

        user_skill = self._fetchone(
            "SELECT * FROM user_skills WHERE user_id=? AND skill_id=?",
            (user_id, skill_id),
        )
        curr_xp = (user_skill["current_xp"] or 0) + xp
        curr_level = user_skill["current_level"] or 0
        total_xp = (user_skill["total_xp"] or 0) + xp
        leveled_up = False

        while curr_xp >= xp_per_level and curr_level < max_level:
            curr_xp -= xp_per_level
            curr_level += 1
            leveled_up = True

        if curr_level >= max_level:
            curr_xp = min(curr_xp, xp_per_level)   # cap at max

        self._execute(
            """UPDATE user_skills SET current_level=?, current_xp=?, total_xp=?,
               updated_at=datetime('now','localtime')
               WHERE user_id=? AND skill_id=?""",
            (curr_level, curr_xp, total_xp, user_id, skill_id),
        )
        self._commit()
        return {"leveled_up": leveled_up, "new_level": curr_level, "new_xp": curr_xp}

    def get_skill(self, user_id: int, skill_slug: str) -> Skill | None:
        row = self._fetchone(
            """SELECT s.*, us.current_level, us.current_xp, us.total_xp
               FROM skills s
               LEFT JOIN user_skills us ON us.skill_id=s.id AND us.user_id=?
               WHERE s.slug=?""",
            (user_id, skill_slug),
        )
        if not row:
            return None
        return Skill(
            id=row["id"], slug=row["slug"], name=row["name"],
            description=row["description"] or "",
            icon=row["icon"] or "star",
            max_level=row["max_level"], xp_per_level=row["xp_per_level"],
            current_level=row["current_level"] or 0,
            current_xp=row["current_xp"] or 0,
            total_xp=row["total_xp"] or 0,
        )
