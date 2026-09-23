"""Gamification service — XP, skills, badges, accountability score."""
from __future__ import annotations
from database.repositories import (
    SkillRepository, BadgeRepository, TaskRepository,
    PomodoroRepository, FlashcardStudySessionRepository, AccountabilityRepository,
)
from models import Badge, Skill
from utils.logger import get_logger
from utils import today, fmt_date, start_of_week, end_of_week, percentage, clamp

log = get_logger(__name__)
_skill_repo = SkillRepository()
_badge_repo = BadgeRepository()
_task_repo = TaskRepository()
_pomo_repo = PomodoroRepository()
_fc_repo = FlashcardStudySessionRepository()
_acc_repo = AccountabilityRepository()


# ── XP & Skills ────────────────────────────────────────────────────────────

def award_xp(user_id: int, skill_slug: str, xp: int) -> dict:
    """Award XP to a skill; return level-up info dict."""
    return _skill_repo.add_xp(user_id, skill_slug, xp)


def get_skills(user_id: int) -> list[Skill]:
    return _skill_repo.get_all_with_progress(user_id)


# ── Badges ─────────────────────────────────────────────────────────────────

TRIGGER_CHECKS: dict[str, list[str]] = {
    "task_complete":     ["first_task", "task_master_10", "task_master_50",
                          "task_master_100", "no_late_week", "all_subjects",
                          "night_owl", "early_bird"],
    "pomodoro_complete": ["first_pomodoro", "pomodoro_10", "pomodoro_50",
                          "study_hour_5", "study_hour_25", "study_hour_100"],
    "flashcard_session": ["first_deck", "flashcard_100", "perfect_session"],
    "streak_update":     ["streak_7", "streak_30", "streak_100", "comeback"],
    "schedule_add":      ["first_schedule"],
    "daily":             ["acc_90_week", "acc_perfect_day", "task_streak_3"],
}


def check_and_unlock_badges(user_id: int, trigger: str = "daily") -> list[str]:
    """
    Run all badge checks relevant to *trigger*.
    Returns list of newly-unlocked badge slugs.
    """
    slugs_to_check = TRIGGER_CHECKS.get(trigger, [])
    unlocked: list[str] = []
    for slug in slugs_to_check:
        if not _badge_repo.is_unlocked(user_id, slug):
            if _meets_criteria(user_id, slug):
                badge = _badge_repo.unlock(user_id, slug)
                if badge:
                    unlocked.append(slug)
                    log.info("Badge unlocked: %s for user %d", slug, user_id)
                    # Award XP for the badge itself
                    award_xp(user_id, "discipline", badge.xp_reward // 2)
    return unlocked


def get_badges(user_id: int) -> list[Badge]:
    return _badge_repo.get_all_with_status(user_id)


def get_recent_badges(user_id: int, limit: int = 5) -> list[Badge]:
    return _badge_repo.get_recent(user_id, limit)


def get_badge_count(user_id: int) -> int:
    return _badge_repo.count_unlocked(user_id)


# ── Accountability score ────────────────────────────────────────────────────

def calculate_accountability_score(user_id: int) -> dict:
    """
    Compute today's accountability score (0–100) from five factors:

    1. Task completion rate (30 pts)
    2. Late tasks penalty (20 pts)
    3. Study hours (25 pts)
    4. Flashcard accuracy (15 pts)
    5. Consistency / streak (10 pts)
    """
    start = fmt_date(start_of_week())
    end   = fmt_date(today())

    # Factor 1: task completion this week
    total_tasks = _task_repo.count(
        "user_id=? AND created_at >= date('now','-7 days')", (user_id,)
    )
    done_tasks = _task_repo.count_completed_between(user_id, start, end)
    task_rate = (done_tasks / max(total_tasks, 1))
    task_score = round(task_rate * 30, 2)

    # Factor 2: late tasks (penalty)
    late_tasks = _task_repo.count_late_between(user_id, start, end)
    late_penalty = min(late_tasks * 4, 20)
    late_score = round(20 - late_penalty, 2)

    # Factor 3: study hours (target 10 h/week = 600 min)
    study_min = _pomo_repo.total_work_minutes(user_id, start, end)
    study_rate = clamp(study_min / 600, 0, 1)
    study_score = round(study_rate * 25, 2)

    # Factor 4: flashcard accuracy this week
    fc_acc = _fc_repo.average_accuracy(user_id, start, end)
    fc_score = round(fc_acc * 15, 2)

    # Factor 5: streak consistency
    from services.streak_service import get_current_streak
    streak = get_current_streak(user_id)
    streak_score = round(min(streak / 7, 1) * 10, 2)

    total = clamp(task_score + late_score + study_score + fc_score + streak_score, 0, 100)
    breakdown = {
        "task_completion": task_score,
        "punctuality":     late_score,
        "study_hours":     study_score,
        "flashcard_accuracy": fc_score,
        "consistency":     streak_score,
        "total":           round(total, 2),
    }
    _acc_repo.upsert(user_id, fmt_date(today()), total, breakdown)
    return breakdown


def get_accountability_history(user_id: int, days: int = 30) -> list[dict]:
    entries = _acc_repo.get_history(user_id, days)
    return [{"date": e.date, "score": e.score} for e in entries]


def get_today_accountability(user_id: int) -> float:
    entry = _acc_repo.get_today(user_id)
    if entry:
        return entry.score
    data = calculate_accountability_score(user_id)
    return data["total"]


# ── Private badge criteria checks ─────────────────────────────────────────

def _meets_criteria(user_id: int, slug: str) -> bool:  # noqa: C901
    from datetime import datetime
    from services.streak_service import get_current_streak
    h = datetime.now().hour

    done_total = _task_repo.count("user_id=? AND status='done'", (user_id,))
    all_sessions = _pomo_repo.total_sessions(
        user_id,
        "2000-01-01",
        fmt_date(today()),
    )
    study_min = _pomo_repo.total_work_minutes(user_id, "2000-01-01", fmt_date(today()))

    match slug:
        case "first_task":        return done_total >= 1
        case "task_master_10":    return done_total >= 10
        case "task_master_50":    return done_total >= 50
        case "task_master_100":   return done_total >= 100
        case "first_pomodoro":    return all_sessions >= 1
        case "pomodoro_10":       return all_sessions >= 10
        case "pomodoro_50":       return all_sessions >= 50
        case "study_hour_5":      return study_min >= 300
        case "study_hour_25":     return study_min >= 1500
        case "study_hour_100":    return study_min >= 6000
        case "streak_7":          return get_current_streak(user_id) >= 7
        case "streak_30":         return get_current_streak(user_id) >= 30
        case "streak_100":        return get_current_streak(user_id) >= 100
        case "flashcard_100":     return _fc_repo.total_correct(user_id) >= 100
        case "all_subjects":      return _task_repo.get_distinct_subject_count(user_id) >= 5
        case "night_owl":         return h >= 22 and done_total >= 1
        case "early_bird":        return h < 7 and done_total >= 1
        case "acc_perfect_day":
            e = _acc_repo.get_today(user_id)
            return e is not None and e.score >= 99.9
        case "acc_90_week":       return _acc_repo.weekly_average(user_id) >= 90
        case "no_late_week":
            start = fmt_date(start_of_week()); end = fmt_date(today())
            return _task_repo.count_late_between(user_id, start, end) == 0
        case "task_streak_3":
            # Three consecutive days of task completion — use streak proxy
            return get_current_streak(user_id) >= 3
        case "first_schedule":
            from database.repositories import ScheduleRepository
            return ScheduleRepository().count_for_user(user_id) >= 1
        case "perfect_session":
            sessions = _fc_repo.get_history(user_id, limit=5)
            return any(s.accuracy >= 1.0 and s.total_cards >= 5 for s in sessions)
        case "comeback":
            from services.streak_service import missed_yesterday
            return get_current_streak(user_id) >= 1 and not missed_yesterday(user_id)
        case "first_deck":
            from database.repositories import FlashcardDeckRepository
            return FlashcardDeckRepository().count("user_id=?", (user_id,)) >= 1
        case _:
            return False
