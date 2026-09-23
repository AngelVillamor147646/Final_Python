"""Task repository — full CRUD, filtering, search, sort, recurring."""
from __future__ import annotations
import sqlite3
from datetime import date
from typing import Optional
from database.repositories.base import BaseRepository
from models import Task
from utils.date_utils import fmt_date


class TaskRepository(BaseRepository[Task]):
    TABLE = "tasks"

    def _row_to_model(self, row: sqlite3.Row) -> Task:
        return Task(
            id=row["id"], user_id=row["user_id"], title=row["title"],
            subject_id=row["subject_id"], description=row["description"] or "",
            priority=row["priority"], status=row["status"],
            label_color=row["label_color"] or "#7C4DFF",
            deadline=row["deadline"], reminder_at=row["reminder_at"],
            is_recurring=bool(row["is_recurring"]),
            recur_rule=row["recur_rule"],
            parent_task_id=row["parent_task_id"],
            sort_order=row["sort_order"] or 0,
            completed_at=row["completed_at"],
            created_at=row["created_at"], updated_at=row["updated_at"],
        )

    def create(
        self, user_id: int, title: str, subject_id: Optional[int] = None,
        description: str = "", priority: str = "medium",
        label_color: str = "#7C4DFF", deadline: Optional[str] = None,
        reminder_at: Optional[str] = None, is_recurring: bool = False,
        recur_rule: Optional[str] = None, parent_task_id: Optional[int] = None,
    ) -> Task:
        row_id = self._insert({
            "user_id": user_id, "title": title, "subject_id": subject_id,
            "description": description, "priority": priority,
            "label_color": label_color, "deadline": deadline,
            "reminder_at": reminder_at,
            "is_recurring": 1 if is_recurring else 0,
            "recur_rule": recur_rule, "parent_task_id": parent_task_id,
        })
        return self.get_by_id(row_id)  # type: ignore[return-value]

    def update(
        self, task_id: int, title: str, subject_id: Optional[int],
        description: str, priority: str, label_color: str,
        deadline: Optional[str], reminder_at: Optional[str],
        is_recurring: bool, recur_rule: Optional[str],
    ) -> bool:
        cur = self._execute(
            """UPDATE tasks SET title=?, subject_id=?, description=?,
               priority=?, label_color=?, deadline=?, reminder_at=?,
               is_recurring=?, recur_rule=?,
               updated_at=datetime('now','localtime') WHERE id=?""",
            (title, subject_id, description, priority, label_color,
             deadline, reminder_at, 1 if is_recurring else 0,
             recur_rule, task_id),
        )
        self._commit()
        return cur.rowcount > 0

    def mark_done(self, task_id: int) -> bool:
        cur = self._execute(
            """UPDATE tasks SET status='done',
               completed_at=datetime('now','localtime'),
               updated_at=datetime('now','localtime') WHERE id=?""",
            (task_id,),
        )
        self._commit()
        return cur.rowcount > 0

    def mark_status(self, task_id: int, status: str) -> bool:
        completed_at = "datetime('now','localtime')" if status == "done" else "NULL"
        cur = self._execute(
            f"""UPDATE tasks SET status=?,
                completed_at={completed_at},
                updated_at=datetime('now','localtime') WHERE id=?""",
            (status, task_id),
        )
        self._commit()
        return cur.rowcount > 0

    def get_for_user(
        self,
        user_id: int,
        status: Optional[str] = None,
        subject_id: Optional[int] = None,
        priority: Optional[str] = None,
        search: str = "",
        order_by: str = "deadline ASC, created_at DESC",
    ) -> list[Task]:
        conditions = ["user_id = ?"]
        params: list = [user_id]
        if status:
            conditions.append("status = ?")
            params.append(status)
        if subject_id is not None:
            conditions.append("subject_id = ?")
            params.append(subject_id)
        if priority:
            conditions.append("priority = ?")
            params.append(priority)
        if search:
            conditions.append("(title LIKE ? OR description LIKE ?)")
            like = f"%{search}%"
            params += [like, like]
        where = " AND ".join(conditions)
        rows = self._fetchall(
            f"SELECT * FROM tasks WHERE {where} ORDER BY {order_by}",
            tuple(params),
        )
        return self._rows_to_models(rows)

    def get_due_today(self, user_id: int) -> list[Task]:
        today = fmt_date(date.today())
        rows = self._fetchall(
            """SELECT * FROM tasks
               WHERE user_id=? AND date(deadline)=? AND status NOT IN ('done','cancelled')
               ORDER BY priority DESC, deadline ASC""",
            (user_id, today),
        )
        return self._rows_to_models(rows)

    def get_upcoming(self, user_id: int, days: int = 7) -> list[Task]:
        rows = self._fetchall(
            """SELECT * FROM tasks
               WHERE user_id=? AND deadline IS NOT NULL
               AND date(deadline) BETWEEN date('now') AND date('now', ?||' days')
               AND status NOT IN ('done','cancelled')
               ORDER BY deadline ASC""",
            (user_id, str(days)),
        )
        return self._rows_to_models(rows)

    def get_overdue(self, user_id: int) -> list[Task]:
        rows = self._fetchall(
            """SELECT * FROM tasks
               WHERE user_id=? AND deadline IS NOT NULL
               AND date(deadline) < date('now')
               AND status NOT IN ('done','cancelled')
               ORDER BY deadline ASC""",
            (user_id,),
        )
        return self._rows_to_models(rows)

    def get_completed_today(self, user_id: int) -> list[Task]:
        rows = self._fetchall(
            """SELECT * FROM tasks
               WHERE user_id=? AND status='done'
               AND date(completed_at)=date('now')""",
            (user_id,),
        )
        return self._rows_to_models(rows)

    def count_completed_between(self, user_id: int, start: str, end: str) -> int:
        row = self._fetchone(
            """SELECT COUNT(*) AS n FROM tasks
               WHERE user_id=? AND status='done'
               AND date(completed_at) BETWEEN ? AND ?""",
            (user_id, start, end),
        )
        return row["n"] if row else 0

    def count_late_between(self, user_id: int, start: str, end: str) -> int:
        """Tasks completed after their deadline OR still overdue."""
        row = self._fetchone(
            """SELECT COUNT(*) AS n FROM tasks
               WHERE user_id=?
               AND deadline IS NOT NULL
               AND date(deadline) BETWEEN ? AND ?
               AND (
                   (status='done' AND date(completed_at) > date(deadline))
                   OR (status NOT IN ('done','cancelled') AND date(deadline) < date('now'))
               )""",
            (user_id, start, end),
        )
        return row["n"] if row else 0

    def get_recurring(self, user_id: int) -> list[Task]:
        rows = self._fetchall(
            "SELECT * FROM tasks WHERE user_id=? AND is_recurring=1", (user_id,)
        )
        return self._rows_to_models(rows)

    def get_distinct_subject_count(self, user_id: int) -> int:
        row = self._fetchone(
            """SELECT COUNT(DISTINCT subject_id) AS n FROM tasks
               WHERE user_id=? AND subject_id IS NOT NULL""",
            (user_id,),
        )
        return row["n"] if row else 0
