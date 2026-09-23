"""Views package __init__."""
from views.screens.splash_screen    import SplashScreen
from views.screens.onboarding_screen import OnboardingScreen
from views.screens.main_screen      import MainScreen
from views.screens.dashboard_screen import DashboardScreen
from views.screens.task_screen      import TaskScreen
from views.screens.schedule_screen  import ScheduleScreen
from views.screens.pomodoro_screen  import PomodoroScreen
from views.screens.flashcard_screen import FlashcardScreen
from views.screens.statistics_screen import StatisticsScreen
from views.screens.badges_screen    import BadgesScreen
from views.screens.skills_screen    import SkillsScreen
from views.screens.reflection_screen import ReflectionScreen
from views.screens.settings_screen  import SettingsScreen

__all__ = [
    "SplashScreen", "OnboardingScreen", "MainScreen",
    "DashboardScreen", "TaskScreen", "ScheduleScreen",
    "PomodoroScreen", "FlashcardScreen", "StatisticsScreen",
    "BadgesScreen", "SkillsScreen", "ReflectionScreen", "SettingsScreen",
]
