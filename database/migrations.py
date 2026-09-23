"""
Tasklyn — Database Migration Runner
======================================
Version-based migration system. Each migration is a plain function that
receives the connection and performs schema alterations.  Migrations are
idempotent and run exactly once per database.
"""
from __future__ import annotations

from typing import Callable

from database.connection import execute, commit, fetchone
from utils.logger import get_logger

log = get_logger(__name__)

MigrationFn = Callable[[], None]


# ---------------------------------------------------------------------------
# Migration registry
# ---------------------------------------------------------------------------

_MIGRATIONS: dict[int, MigrationFn] = {}


def migration(version: int):
    """Decorator to register a migration at *version*."""
    def _decorator(fn: MigrationFn) -> MigrationFn:
        _MIGRATIONS[version] = fn
        return fn
    return _decorator


# ---------------------------------------------------------------------------
# Registered migrations
# ---------------------------------------------------------------------------

@migration(1)
def _seed_default_data() -> None:
    """
    Seed static reference data:
    - 5 skill definitions
    - 25 badge definitions
    """
    # ---------- Skills ----------
    skills = [
        ("time_management", "Time Management",
         "Complete tasks before their deadlines.", "clock-outline", 10, 120),
        ("consistency",     "Consistency",
         "Study or complete tasks every day.",     "calendar-check",10, 100),
        ("focus",           "Focus",
         "Complete Pomodoro sessions without interruption.", "bullseye-arrow", 10, 100),
        ("productivity",    "Productivity",
         "Close a high volume of tasks per week.", "rocket-launch",  10, 110),
        ("discipline",      "Discipline",
         "Maintain streaks and high accountability scores.", "shield-star", 10, 130),
    ]
    for slug, name, desc, icon, max_lvl, xp_per in skills:
        execute(
            """
            INSERT OR IGNORE INTO skills
                (slug, name, description, icon, max_level, xp_per_level)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (slug, name, desc, icon, max_lvl, xp_per),
        )

    # ---------- Badges ----------
    badges = [
        # slug, name, description, icon, category, xp, hidden
        ("first_task",       "First Step",        "Complete your first task.",            "checkbox-marked-circle", "tasks",     25, 0),
        ("task_streak_3",    "On a Roll",          "Complete tasks 3 days in a row.",      "fire",                   "tasks",     50, 0),
        ("task_master_10",   "Task Master",        "Complete 10 tasks.",                   "trophy",                 "tasks",     75, 0),
        ("task_master_50",   "Centurion",          "Complete 50 tasks.",                   "trophy-award",           "tasks",    150, 0),
        ("task_master_100",  "Legend",             "Complete 100 tasks.",                  "star-shooting",          "tasks",    300, 0),
        ("no_late_week",     "Punctual",           "Zero late tasks in a week.",           "alarm-check",            "tasks",     75, 0),
        ("first_pomodoro",   "In the Zone",        "Complete your first Pomodoro.",        "timer",                  "pomodoro",  25, 0),
        ("pomodoro_10",      "Flow State",         "Complete 10 Pomodoro sessions.",       "timer-sand",             "pomodoro",  75, 0),
        ("pomodoro_50",      "Deep Worker",        "Complete 50 Pomodoro sessions.",       "brain",                  "pomodoro", 150, 0),
        ("study_hour_5",     "Dedicated",          "Log 5 total study hours.",             "book-open-variant",      "study",     50, 0),
        ("study_hour_25",    "Scholar",            "Log 25 total study hours.",            "school",                 "study",    100, 0),
        ("study_hour_100",   "Academic Titan",     "Log 100 total study hours.",           "crown",                  "study",    250, 0),
        ("first_deck",       "Flash!",             "Create your first flashcard deck.",    "cards",                  "flashcards",25, 0),
        ("flashcard_100",    "Memory Palace",      "Answer 100 flashcards correctly.",     "head-lightbulb",         "flashcards",100, 0),
        ("perfect_session",  "Perfect Score",      "Achieve 100% accuracy in a session.", "check-decagram",         "flashcards",100, 0),
        ("streak_7",         "Week Warrior",       "Maintain a 7-day streak.",             "fire",                   "streaks",   75, 0),
        ("streak_30",        "Monthly Legend",     "Maintain a 30-day streak.",            "fire-circle",            "streaks",  200, 0),
        ("streak_100",       "Unstoppable",        "Maintain a 100-day streak.",           "infinity",               "streaks",  500, 0),
        ("acc_90_week",      "High Achiever",      "Accountability score ≥ 90 for a week.","chart-line",             "account",  100, 0),
        ("acc_perfect_day",  "Flawless",           "Score 100 accountability in a day.",   "shield-check",           "account",   75, 0),
        ("all_subjects",     "Well-Rounded",       "Add tasks for 5+ different subjects.", "book-multiple",          "general",   50, 0),
        ("night_owl",        "Night Owl",          "Complete a task after 10 PM.",         "owl",                    "general",   25, 0),
        ("early_bird",       "Early Bird",         "Complete a task before 7 AM.",         "weather-sunny",          "general",   25, 0),
        ("first_schedule",   "Organized",          "Add your first class to the schedule.","calendar-month",         "schedule",  25, 0),
        ("comeback",         "Comeback Kid",       "Resume a streak after missing a day.", "restore",                "streaks",   50, 0),
    ]
    for row in badges:
        execute(
            """
            INSERT OR IGNORE INTO badges
                (slug, name, description, icon, category, xp_reward, is_hidden)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            row,
        )

    commit()
    log.info("Seed data inserted (migration 1).")


# ---------------------------------------------------------------------------
# Runner
# ---------------------------------------------------------------------------

def _current_version() -> int:
    row = fetchone("SELECT MAX(version) AS v FROM db_migrations")
    return row["v"] if row and row["v"] is not None else 0


def run_migrations() -> None:
    """Run all pending migrations in version order."""
    current = _current_version()
    pending = sorted(v for v in _MIGRATIONS if v > current)

    if not pending:
        log.debug("Database is up to date (version %d).", current)
        return

    for version in pending:
        log.info("Applying migration v%d…", version)
        try:
            _MIGRATIONS[version]()
            execute(
                "INSERT INTO db_migrations (version) VALUES (?)",
                (version,),
            )
            commit()
            log.info("Migration v%d applied.", version)
        except Exception as exc:
            log.error("Migration v%d FAILED: %s", version, exc, exc_info=True)
            raise
