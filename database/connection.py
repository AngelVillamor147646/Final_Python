"""
Tasklyn — SQLite Connection Manager
======================================
Thread-safe SQLite connection manager with WAL mode, FK enforcement,
and automatic schema migration on startup.
"""
from __future__ import annotations

import sqlite3
import threading
from pathlib import Path
from typing import Any, Iterator

from utils.logger import get_logger

log = get_logger(__name__)

# One connection per thread (SQLite is not thread-safe in shared mode)
_local = threading.local()


def _get_db_path() -> Path:
    """Resolve the database path from config (lazy import avoids circulars)."""
    from config import DATABASE_PATH  # type: ignore[import]
    return DATABASE_PATH


def get_connection() -> sqlite3.Connection:
    """
    Return the thread-local SQLite connection, creating it on first access.

    Settings applied:
    - WAL journal mode (faster concurrent reads)
    - Foreign keys enforced
    - Row factory → sqlite3.Row for dict-like access
    - Busy timeout of 5 s to handle contention
    """
    conn = getattr(_local, "conn", None)
    if conn is None:
        db_path = _get_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path), check_same_thread=False)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA foreign_keys=ON;")
        conn.execute("PRAGMA busy_timeout=5000;")
        conn.execute("PRAGMA cache_size=-8000;")   # 8 MB cache
        _local.conn = conn
        log.debug("SQLite connection opened: %s", db_path)
    return conn


def close_connection() -> None:
    """Close the thread-local connection if open."""
    conn = getattr(_local, "conn", None)
    if conn:
        conn.close()
        _local.conn = None
        log.debug("SQLite connection closed.")


def execute(sql: str, params: tuple = ()) -> sqlite3.Cursor:
    """Execute a single statement on the thread-local connection."""
    return get_connection().execute(sql, params)


def executemany(sql: str, params_seq: list[tuple]) -> sqlite3.Cursor:
    """Execute a statement for each param tuple."""
    return get_connection().executemany(sql, params_seq)


def commit() -> None:
    """Commit the current transaction."""
    get_connection().commit()


def rollback() -> None:
    """Roll back the current transaction."""
    get_connection().rollback()


class transaction:
    """
    Context manager that wraps a block of SQL in a single transaction.

    Usage::

        with transaction():
            execute("INSERT INTO tasks ...", (...,))
            execute("UPDATE subjects ...", (...,))
    """

    def __enter__(self) -> "transaction":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> bool:
        if exc_type is None:
            commit()
        else:
            rollback()
            log.error("Transaction rolled back due to: %s", exc_val)
        return False   # don't suppress exceptions


def fetchone(sql: str, params: tuple = ()) -> sqlite3.Row | None:
    """Execute *sql* and return a single row or None."""
    return execute(sql, params).fetchone()


def fetchall(sql: str, params: tuple = ()) -> list[sqlite3.Row]:
    """Execute *sql* and return all rows."""
    return execute(sql, params).fetchall()


def init_database() -> None:
    """
    Bootstrap the database: create schema then run any pending migrations.
    Called once at application startup.
    """
    from database.schema import create_all_tables
    from database.migrations import run_migrations

    log.info("Initialising database…")
    create_all_tables()
    run_migrations()
    log.info("Database ready.")
