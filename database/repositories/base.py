"""
Tasklyn — Base Repository
===========================
Generic CRUD base that all domain repositories inherit from.
Provides type-safe helpers for common SQL patterns.
"""
from __future__ import annotations

import sqlite3
from typing import Any, Generic, Optional, TypeVar

from database.connection import execute, fetchall, fetchone, commit
from utils.logger import get_logger

log = get_logger(__name__)

T = TypeVar("T")


class BaseRepository(Generic[T]):
    """
    Base repository providing generic CRUD helpers.

    Sub-classes must set:
      - ``TABLE``: the database table name
      - ``_row_to_model``: convert sqlite3.Row → domain model
    """

    TABLE: str = ""

    # ------------------------------------------------------------------
    # Protected helpers
    # ------------------------------------------------------------------

    def _execute(self, sql: str, params: tuple = ()) -> sqlite3.Cursor:
        return execute(sql, params)

    def _fetchone(self, sql: str, params: tuple = ()) -> Optional[sqlite3.Row]:
        return fetchone(sql, params)

    def _fetchall(self, sql: str, params: tuple = ()) -> list[sqlite3.Row]:
        return fetchall(sql, params)

    def _commit(self) -> None:
        commit()

    def _row_to_model(self, row: sqlite3.Row) -> T:  # type: ignore[return]
        raise NotImplementedError

    def _rows_to_models(self, rows: list[sqlite3.Row]) -> list[T]:
        return [self._row_to_model(r) for r in rows]

    # ------------------------------------------------------------------
    # Generic CRUD
    # ------------------------------------------------------------------

    def get_by_id(self, record_id: int) -> Optional[T]:
        row = self._fetchone(
            f"SELECT * FROM {self.TABLE} WHERE id = ?", (record_id,)
        )
        return self._row_to_model(row) if row else None

    def get_all(self) -> list[T]:
        rows = self._fetchall(f"SELECT * FROM {self.TABLE}")
        return self._rows_to_models(rows)

    def delete_by_id(self, record_id: int) -> bool:
        cur = self._execute(
            f"DELETE FROM {self.TABLE} WHERE id = ?", (record_id,)
        )
        self._commit()
        return cur.rowcount > 0

    def count(self, where: str = "", params: tuple = ()) -> int:
        sql = f"SELECT COUNT(*) AS n FROM {self.TABLE}"
        if where:
            sql += f" WHERE {where}"
        row = self._fetchone(sql, params)
        return row["n"] if row else 0

    def exists(self, where: str, params: tuple = ()) -> bool:
        return self.count(where, params) > 0

    # ------------------------------------------------------------------
    # Generic update helper
    # ------------------------------------------------------------------

    def _update_fields(
        self,
        record_id: int,
        fields: dict[str, Any],
    ) -> bool:
        """
        Build and execute an UPDATE statement for the given *fields* dict.
        Automatically sets ``updated_at`` if the table has that column.
        """
        if not fields:
            return False
        # Add updated_at timestamp if not already provided
        fields.setdefault("updated_at", "datetime('now','localtime')")
        set_clause = ", ".join(
            f"{k} = {v!r}" if isinstance(v, str) and "datetime" in v
            else f"{k} = ?"
            for k, v in fields.items()
        )
        values = [
            v for v in fields.values()
            if not (isinstance(v, str) and "datetime" in v)
        ]
        values.append(record_id)
        cur = self._execute(
            f"UPDATE {self.TABLE} SET {set_clause} WHERE id = ?",
            tuple(values),
        )
        self._commit()
        return cur.rowcount > 0

    # ------------------------------------------------------------------
    # Convenience insert helper
    # ------------------------------------------------------------------

    def _insert(self, fields: dict[str, Any]) -> int:
        """
        Build and execute an INSERT statement; return the new row id.
        Values that are the literal string ``"NOW"`` are replaced with the
        SQLite ``datetime('now','localtime')`` expression.
        """
        cols = list(fields.keys())
        vals = list(fields.values())
        placeholders = ", ".join("?" for _ in cols)
        col_str = ", ".join(cols)
        cur = self._execute(
            f"INSERT INTO {self.TABLE} ({col_str}) VALUES ({placeholders})",
            tuple(vals),
        )
        self._commit()
        return cur.lastrowid  # type: ignore[return-value]
