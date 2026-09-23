"""Database repositories package."""
from database.repositories.user_repo import UserRepository
from database.repositories.subject_repo import SubjectRepository
from database.repositories.task_repo import TaskRepository
from database.repositories.schedule_repo import ScheduleRepository
from database.repositories.pomodoro_repo import PomodoroRepository
from database.repositories.flashcard_repo import (
    FlashcardDeckRepository,
    FlashcardRepository,
    FlashcardStudySessionRepository,
)
from database.repositories.badge_repo import BadgeRepository
from database.repositories.skill_repo import SkillRepository
from database.repositories.streak_repo import StreakRepository
from database.repositories.settings_repo import SettingsRepository, NotificationRepository
from database.repositories.accountability_repo import AccountabilityRepository

__all__ = [
    "UserRepository", "SubjectRepository", "TaskRepository",
    "ScheduleRepository", "PomodoroRepository",
    "FlashcardDeckRepository", "FlashcardRepository",
    "FlashcardStudySessionRepository",
    "BadgeRepository", "SkillRepository", "StreakRepository",
    "SettingsRepository", "NotificationRepository",
    "AccountabilityRepository",
]
