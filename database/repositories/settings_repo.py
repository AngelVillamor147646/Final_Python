"""Settings repository — key-value store per user."""
from __future__ import annotations
import sqlite3
from typing import Any, Optional
from database.repositories.base import BaseRepository
from models import Setting
from utils.helpers import safe_json_loads, safe_json_dumps


class SettingsRepository(BaseRepository[Setting]):
    TABLE = "settings"

    # Default values for all known keys
    DEFAULTS: dict[str, str] = {
        "theme":                "Dark",
        "primary_hue":          "DeepPurple",
        "accent_hue":           "Amber",
        "font_size":            "medium",
        "notifications_enabled":"1",
        "pomodoro_work":        "25",
        "pomodoro_break":       "5",
        "pomodoro_long_break":  "15",
        "pomodoro_sessions":    "4",
        "reminder_default_min": "15",
        "auto_backup":          "1",
    }

    def _row_to_model(self, row: sqlite3.Row) -> Setting:
        return Setting(
            id=row["id"], user_id=row["user_id"],
            key=row["key"], value=row["value"],
            updated_at=row["updated_at"],
        )

    def get(self, user_id: int, key: str) -> str:
        row = self._fetchone(
            "SELECT * FROM settings WHERE user_id=? AND key=?",
            (user_id, key),
        )
        if row:
            return row["value"]
        return self.DEFAULTS.get(key, "")

    def get_int(self, user_id: int, key: str) -> int:
        try:
            return int(self.get(user_id, key))
        except ValueError:
            return 0

    def get_bool(self, user_id: int, key: str) -> bool:
        return self.get(user_id, key) in ("1", "true", "True", "yes")

    def get_json(self, user_id: int, key: str) -> Any:
        return safe_json_loads(self.get(user_id, key))

    def set(self, user_id: int, key: str, value: str) -> None:
        self._execute(
            """INSERT INTO settings (user_id, key, value)
               VALUES (?, ?, ?)
               ON CONFLICT(user_id, key) DO UPDATE SET
               value=excluded.value,
               updated_at=datetime('now','localtime')""",
            (user_id, key, value),
        )
        self._commit()

    def set_json(self, user_id: int, key: str, value: Any) -> None:
        self.set(user_id, key, safe_json_dumps(value))

    def get_all_for_user(self, user_id: int) -> dict[str, str]:
        rows = self._fetchall(
            "SELECT key, value FROM settings WHERE user_id=?", (user_id,)
        )
        result = dict(self.DEFAULTS)
        result.update({r["key"]: r["value"] for r in rows})
        return result

    def reset_to_defaults(self, user_id: int) -> None:
        self._execute("DELETE FROM settings WHERE user_id=?", (user_id,))
        self._commit()


# ------------------------------------------------------------------ notifications
class NotificationRepository(BaseRepository):
    TABLE = "notifications"

    def _row_to_model(self, row: sqlite3.Row):  # type: ignore[override]
        from models import Notification
        return Notification(
            id=row["id"], user_id=row["user_id"],
            notif_type=row["notif_type"], ref_id=row["ref_id"],
            title=row["title"], body=row["body"],
            scheduled_at=row["scheduled_at"],
            is_sent=bool(row["is_sent"]),
            created_at=row["created_at"],
        )

    def schedule(
        self, user_id: int, notif_type: str, title: str, body: str,
        scheduled_at: str, ref_id: Optional[int] = None,
    ) -> int:
        return self._insert({
            "user_id": user_id, "notif_type": notif_type,
            "ref_id": ref_id, "title": title, "body": body,
            "scheduled_at": scheduled_at,
        })

    def get_pending(self, user_id: int) -> list:
        rows = self._fetchall(
            """SELECT * FROM notifications
               WHERE user_id=? AND is_sent=0
               AND scheduled_at <= datetime('now','localtime')
               ORDER BY scheduled_at""",
            (user_id,),
        )
        return self._rows_to_models(rows)

    def mark_sent(self, notif_id: int) -> None:
        self._execute("UPDATE notifications SET is_sent=1 WHERE id=?", (notif_id,))
        self._commit()

    def delete_for_ref(self, ref_id: int, notif_type: str) -> None:
        self._execute(
            "DELETE FROM notifications WHERE ref_id=? AND notif_type=?",
            (ref_id, notif_type),
        )
        self._commit()

    def cleanup_sent(self, user_id: int, keep_days: int = 7) -> None:
        self._execute(
            """DELETE FROM notifications
               WHERE user_id=? AND is_sent=1
               AND scheduled_at < datetime('now', ?||' days')""",
            (user_id, f"-{keep_days}"),
        )
        self._commit()
