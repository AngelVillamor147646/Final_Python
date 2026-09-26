"""Statistics service — aggregates data for charts and reports."""
from __future__ import annotations
from utils import fmt_date, start_of_week, end_of_week, start_of_month, end_of_month, today
from database.repositories import (
    TaskRepository, PomodoroRepository, FlashcardStudySessionRepository,
    StreakRepository,
)

_task_repo = PomodoroRepository()
_t_repo = TaskRepository()
_pomo_repo = PomodoroRepository()
_fc_repo = FlashcardStudySessionRepository()
_streak_repo = StreakRepository()


def get_weekly_stats(user_id: int) -> dict:
    start = fmt_date(start_of_week())
    end   = fmt_date(end_of_week())
    return _build_stats(user_id, start, end)


def get_monthly_stats(user_id: int) -> dict:
    start = fmt_date(start_of_month())
    end   = fmt_date(end_of_month())
    return _build_stats(user_id, start, end)


def get_range_stats(user_id: int, start: str, end: str) -> dict:
    return _build_stats(user_id, start, end)


def _build_stats(user_id: int, start: str, end: str) -> dict:
    tasks_done  = _t_repo.count_completed_between(user_id, start, end)
    tasks_late  = _t_repo.count_late_between(user_id, start, end)
    study_min   = _pomo_repo.total_work_minutes(user_id, start, end)
    sessions    = _pomo_repo.total_sessions(user_id, start, end)
    fc_acc      = _fc_repo.average_accuracy(user_id, start, end)
    daily_pomo  = _pomo_repo.daily_minutes(user_id, start, end)
    subj_pomo   = _pomo_repo.by_subject(user_id, start, end)

    return {
        "tasks_completed": tasks_done,
        "tasks_late":      tasks_late,
        "study_minutes":   study_min,
        "pomodoro_sessions": sessions,
        "flashcard_accuracy": round(fc_acc * 100, 1),
        "daily_study_minutes": daily_pomo,
        "subject_minutes":  subj_pomo,
        "start": start, "end": end,
    }


def get_yearly_study_hours(user_id: int, year: int) -> list[dict]:
    """Monthly study hours for the whole year — for bar chart."""
    result = []
    for month in range(1, 13):
        from calendar import monthrange
        _, last_day = monthrange(year, month)
        start = f"{year}-{month:02d}-01"
        end   = f"{year}-{month:02d}-{last_day:02d}"
        minutes = _pomo_repo.total_work_minutes(user_id, start, end)
        result.append({"month": month, "hours": round(minutes / 60, 1)})
    return result

def get_analytics_dashboard_stats(user_id: int) -> dict:
    from datetime import date, timedelta
    from database.connection import fetchall
    today_dt = date.today()
    start_week = today_dt - timedelta(days=today_dt.weekday())
    end_week = start_week + timedelta(days=6)
    
    today_str = fmt_date(today_dt)
    start_week_str = fmt_date(start_week)
    end_week_str = fmt_date(end_week)
    
    tasks_today = _t_repo.count_completed_between(user_id, today_str, today_str)
    tasks_week = _t_repo.count_completed_between(user_id, start_week_str, end_week_str)
    
    pomo_today_mins = _pomo_repo.total_work_minutes(user_id, today_str, today_str)
    pomo_today_hours = round(pomo_today_mins / 60, 1)
    
    # Habits maintained
    habits = fetchall("SELECT COUNT(*) as n FROM user_skills WHERE user_id=?", (user_id,))
    total_habits = habits[0]["n"] if habits else 0
    
    # Chart data: tasks done vs overdue per day (for this week)
    daily_stats = []
    best_day = "-"
    best_done = -1
    
    for i in range(7):
        dt = start_week + timedelta(days=i)
        dt_str = fmt_date(dt)
        done = _t_repo.count_completed_between(user_id, dt_str, dt_str)
        # For overdue, it's tasks whose deadline was this date, and they were either completed late or are still not done
        late = _t_repo.count_late_between(user_id, dt_str, dt_str)
        
        day_name = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"][i]
        daily_stats.append({
            "day": day_name,
            "done": done,
            "overdue": late
        })
        
        if done > best_done:
            best_done = done
            best_day = day_name
            
    if best_done == 0:
        best_day = "None"
            
    return {
        "tasks_completed_today": tasks_today,
        "tasks_completed_week": tasks_week,
        "pomodoro_hours_today": pomo_today_hours,
        "most_productive_day": best_day,
        "total_habits": total_habits,
        "chart_data": daily_stats
    }
