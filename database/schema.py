"""
Tasklyn — Complete SQLite Schema
===================================
All CREATE TABLE and CREATE INDEX statements for the application.
Tables are created in dependency order (parents before children).
"""
from __future__ import annotations

from database.connection import execute, commit
from utils.logger import get_logger

log = get_logger(__name__)


# ---------------------------------------------------------------------------
# Individual table definitions
# ---------------------------------------------------------------------------

_TABLES: list[str] = [

    # ------------------------------------------------------------------ users
    """
    CREATE TABLE IF NOT EXISTS users (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        name        TEXT    NOT NULL,
        avatar_id   TEXT    NOT NULL DEFAULT 'boy_neutral',
        gender      TEXT    NOT NULL DEFAULT 'boy',
        password    TEXT,
        created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
        updated_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
    )
    """,

    # --------------------------------------------------------------- subjects
    """
    CREATE TABLE IF NOT EXISTS subjects (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        name        TEXT    NOT NULL,
        color       TEXT    NOT NULL DEFAULT '#7C4DFF',
        instructor  TEXT,
        room        TEXT,
        created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
    )
    """,

    # ------------------------------------------------------------------ tasks
    """
    CREATE TABLE IF NOT EXISTS tasks (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        subject_id      INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
        title           TEXT    NOT NULL,
        description     TEXT    DEFAULT '',
        priority        TEXT    NOT NULL DEFAULT 'medium'
                            CHECK(priority IN ('low','medium','high','critical')),
        status          TEXT    NOT NULL DEFAULT 'pending'
                            CHECK(status IN ('pending','done')),
        label_color     TEXT    DEFAULT '#7C4DFF',
        deadline        TEXT,
        reminder_at     TEXT,
        is_recurring    INTEGER NOT NULL DEFAULT 0,
        recur_rule      TEXT,
        parent_task_id  INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
        sort_order      INTEGER DEFAULT 0,
        completed_at    TEXT,
        created_at      TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
        updated_at      TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
    )
    """,

    # -------------------------------------------------------------- schedules
    """
    CREATE TABLE IF NOT EXISTS schedules (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        subject_id      INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
        title           TEXT    NOT NULL,
        days            TEXT    NOT NULL DEFAULT '[]',
        start_time      TEXT    NOT NULL,
        end_time        TEXT    NOT NULL,
        room            TEXT    DEFAULT '',
        instructor      TEXT    DEFAULT '',
        color           TEXT    DEFAULT '#7C4DFF',
        notes           TEXT    DEFAULT '',
        reminder_minutes INTEGER DEFAULT 15,
        is_active       INTEGER NOT NULL DEFAULT 1,
        created_at      TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
    )
    """,

    # ------------------------------------------------------- pomodoro_sessions
    """
    CREATE TABLE IF NOT EXISTS pomodoro_sessions (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        subject_id      INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
        task_id         INTEGER REFERENCES tasks(id) ON DELETE SET NULL,
        work_minutes    INTEGER NOT NULL DEFAULT 25,
        break_minutes   INTEGER NOT NULL DEFAULT 5,
        started_at      TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
        ended_at        TEXT,
        completed       INTEGER NOT NULL DEFAULT 0,
        interruptions   INTEGER NOT NULL DEFAULT 0,
        notes           TEXT    DEFAULT ''
    )
    """,

    # --------------------------------------------------------- flashcard_decks
    """
    CREATE TABLE IF NOT EXISTS flashcard_decks (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        subject_id  INTEGER REFERENCES subjects(id) ON DELETE SET NULL,
        name        TEXT    NOT NULL,
        description TEXT    DEFAULT '',
        color       TEXT    DEFAULT '#7C4DFF',
        card_count  INTEGER NOT NULL DEFAULT 0,
        created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
        updated_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
    )
    """,

    # -------------------------------------------------------------- flashcards
    """
    CREATE TABLE IF NOT EXISTS flashcards (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        deck_id     INTEGER NOT NULL REFERENCES flashcard_decks(id) ON DELETE CASCADE,
        question    TEXT    NOT NULL,
        answer      TEXT    NOT NULL,
        q_type      TEXT    NOT NULL DEFAULT 'identification'
                        CHECK(q_type IN ('identification','multiple_choice')),
        choices     TEXT    DEFAULT '[]',
        tags        TEXT    DEFAULT '[]',
        difficulty  INTEGER DEFAULT 1 CHECK(difficulty BETWEEN 1 AND 5),
        sort_order  INTEGER DEFAULT 0,
        created_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
    )
    """,

    # --------------------------------------------------- flashcard_study_sessions
    """
    CREATE TABLE IF NOT EXISTS flashcard_study_sessions (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        deck_id     INTEGER NOT NULL REFERENCES flashcard_decks(id) ON DELETE CASCADE,
        started_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
        ended_at    TEXT,
        total_cards INTEGER NOT NULL DEFAULT 0,
        correct     INTEGER NOT NULL DEFAULT 0,
        incorrect   INTEGER NOT NULL DEFAULT 0,
        accuracy    REAL    DEFAULT 0.0
    )
    """,

    # ------------------------------------------------------- flashcard_results
    """
    CREATE TABLE IF NOT EXISTS flashcard_results (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        session_id      INTEGER NOT NULL
                            REFERENCES flashcard_study_sessions(id) ON DELETE CASCADE,
        flashcard_id    INTEGER NOT NULL REFERENCES flashcards(id) ON DELETE CASCADE,
        is_correct      INTEGER NOT NULL DEFAULT 0,
        answered_at     TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
    )
    """,

    # ------------------------------------------------------------------ badges
    """
    CREATE TABLE IF NOT EXISTS badges (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        slug        TEXT    NOT NULL UNIQUE,
        name        TEXT    NOT NULL,
        description TEXT    NOT NULL DEFAULT '',
        icon        TEXT    NOT NULL DEFAULT 'trophy',
        category    TEXT    NOT NULL DEFAULT 'general',
        xp_reward   INTEGER NOT NULL DEFAULT 50,
        is_hidden   INTEGER NOT NULL DEFAULT 0
    )
    """,

    # --------------------------------------------------------------- user_badges
    """
    CREATE TABLE IF NOT EXISTS user_badges (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        badge_id    INTEGER NOT NULL REFERENCES badges(id) ON DELETE CASCADE,
        unlocked_at TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
        UNIQUE(user_id, badge_id)
    )
    """,

    # ------------------------------------------------------------------ skills
    """
    CREATE TABLE IF NOT EXISTS skills (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        slug        TEXT    NOT NULL UNIQUE,
        name        TEXT    NOT NULL,
        description TEXT    NOT NULL DEFAULT '',
        icon        TEXT    NOT NULL DEFAULT 'star',
        max_level   INTEGER NOT NULL DEFAULT 10,
        xp_per_level INTEGER NOT NULL DEFAULT 100,
        reminder_time TEXT DEFAULT '',
        notification_enabled INTEGER NOT NULL DEFAULT 0,
        streak INTEGER NOT NULL DEFAULT 0,
        longest_streak INTEGER NOT NULL DEFAULT 0,
        last_completed TEXT
    )
    """,

    # -------------------------------------------------------------- user_skills
    """
    CREATE TABLE IF NOT EXISTS user_skills (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        skill_name      TEXT    NOT NULL,
        reminder_time   TEXT    DEFAULT '',
        streak          INTEGER NOT NULL DEFAULT 0,
        longest_streak  INTEGER NOT NULL DEFAULT 0,
        last_completed  TEXT,
        notification_enabled INTEGER NOT NULL DEFAULT 0,
        updated_at      TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
        UNIQUE(user_id, skill_name)
    )
    """,

    # ---------------------------------------------------------------- streaks
    """
    CREATE TABLE IF NOT EXISTS streaks (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        date        TEXT    NOT NULL,
        streak_type TEXT    NOT NULL DEFAULT 'daily'
                        CHECK(streak_type IN ('daily','weekly')),
        UNIQUE(user_id, date, streak_type)
    )
    """,

    # -------------------------------------------------- accountability_history
    """
    CREATE TABLE IF NOT EXISTS accountability_history (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        date            TEXT    NOT NULL,
        score           REAL    NOT NULL DEFAULT 0.0,
        breakdown_json  TEXT    NOT NULL DEFAULT '{}',
        created_at      TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
        UNIQUE(user_id, date)
    )
    """,

    # -------------------------------------------------------------- settings
    """
    CREATE TABLE IF NOT EXISTS settings (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        key         TEXT    NOT NULL,
        value       TEXT    NOT NULL DEFAULT '',
        updated_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime')),
        UNIQUE(user_id, key)
    )
    """,

    # ---------------------------------------------------------- notifications
    """
    CREATE TABLE IF NOT EXISTS notifications (
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id         INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
        notif_type      TEXT    NOT NULL,
        ref_id          INTEGER,
        title           TEXT    NOT NULL DEFAULT '',
        body            TEXT    NOT NULL DEFAULT '',
        scheduled_at    TEXT    NOT NULL,
        is_sent         INTEGER NOT NULL DEFAULT 0,
        created_at      TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
    )
    """,

    # ---------------------------------------------------------- db_migrations
    """
    CREATE TABLE IF NOT EXISTS db_migrations (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        version     INTEGER NOT NULL UNIQUE,
        applied_at  TEXT    NOT NULL DEFAULT (datetime('now','localtime'))
    )
    """,
]


# ---------------------------------------------------------------------------
# Index definitions
# ---------------------------------------------------------------------------

_INDEXES: list[str] = [
    "CREATE INDEX IF NOT EXISTS idx_tasks_user_id       ON tasks(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_deadline      ON tasks(deadline)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_status        ON tasks(status)",
    "CREATE INDEX IF NOT EXISTS idx_tasks_subject_id    ON tasks(subject_id)",
    "CREATE INDEX IF NOT EXISTS idx_schedules_user_id   ON schedules(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_schedules_day       ON schedules(day_of_week)",
    "CREATE INDEX IF NOT EXISTS idx_pomodoro_user_id    ON pomodoro_sessions(user_id)",
    "CREATE INDEX IF NOT EXISTS idx_pomodoro_started_at ON pomodoro_sessions(started_at)",
    "CREATE INDEX IF NOT EXISTS idx_flashcards_deck_id  ON flashcards(deck_id)",
    "CREATE INDEX IF NOT EXISTS idx_fc_results_session  ON flashcard_results(session_id)",
    "CREATE INDEX IF NOT EXISTS idx_streaks_user_date   ON streaks(user_id, date)",
    "CREATE INDEX IF NOT EXISTS idx_acc_user_date       ON accountability_history(user_id, date)",
    "CREATE INDEX IF NOT EXISTS idx_notifications_sched ON notifications(scheduled_at, is_sent)",
    "CREATE INDEX IF NOT EXISTS idx_settings_user_key   ON settings(user_id, key)",
]


# ---------------------------------------------------------------------------
# Public entry point
# ---------------------------------------------------------------------------

def create_all_tables() -> None:
    """Create all tables and indexes if they do not exist."""
    log.debug("Creating database tables…")
    for sql in _TABLES:
        execute(sql.strip())
    for sql in _INDEXES:
        execute(sql.strip())
    commit()
    log.debug("Tables and indexes created.")
