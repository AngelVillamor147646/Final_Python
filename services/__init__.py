"""Services package — public re-exports."""
from services.auth_service import (
    is_first_launch, get_active_user, create_profile, update_profile, refresh_active_user,
)
from services.task_service import (
    get_user_tasks, get_today_tasks, get_upcoming_tasks, get_overdue_tasks,
    create_task, update_task, complete_task, delete_task, get_task, get_subjects, create_subject,
)
from services.schedule_service import (
    get_weekly_schedule, get_day_schedule, get_today_classes,
    create_schedule, update_schedule, delete_schedule, toggle_active,
)
from services.pomodoro_service import (
    start_session, complete_session as complete_pomo, abandon_session,
    get_today_summary, get_week_summary, get_history as get_pomo_history,
    get_daily_chart_data, get_subject_breakdown,
)
from services.flashcard_service import (
    get_decks, create_deck, delete_deck, get_cards, get_mistake_cards,
    import_from_markdown, start_study_session, record_answer,
    close_study_session, get_study_history, get_average_accuracy,
)
from services.gamification_service import (
    award_xp, get_skills, check_and_unlock_badges, get_badges,
    get_recent_badges, get_badge_count, calculate_accountability_score,
    get_accountability_history, get_today_accountability,
)
from services.streak_service import (
    record_activity, get_current_streak, get_longest_streak,
    get_total_active_days, get_calendar_data, missed_yesterday, get_streak_summary,
)
from services.notification_service import (
    send_notification, schedule_task_reminder, schedule_class_reminder,
    send_pomodoro_notification, dispatch_pending,
)
from services.statistics_service import (
    get_weekly_stats, get_monthly_stats, get_range_stats, get_yearly_study_hours,
)
from services.backup_service import (
    create_backup, list_backups, restore_backup,
    export_tasks_csv, export_stats_json, export_stats_pdf,
)
