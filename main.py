"""
Tasklyn — Application Entry Point
====================================
Initialises the database, builds the KivyMD app, and starts the
screen manager with Splash → Onboarding/Main routing.
"""
from __future__ import annotations
import os
import sys

# Ensure project root is on the path regardless of working directory
sys.path.insert(0, os.path.dirname(__file__))

# ── Kivy environment (must be set before importing kivy) ──────────────────
os.environ.setdefault("KIVY_NO_ENV_CONFIG", "1")

from kivy.clock import Clock
from kivy.core.window import Window
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, FadeTransition
from kivymd.app import MDApp

from utils.logger import get_logger
from database.connection import init_database
from themes import theme_manager
from config import APP_NAME, APP_VERSION, DEFAULT_THEME

log = get_logger("tasklyn.main")


class TasklynApp(MDApp):
    """Root KivyMD application class."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.title = f"{APP_NAME} v{APP_VERSION}"
        self.icon = "app-icon.png"
        self._user_id: int | None = None

    def build(self):
        # ── Database bootstrap ──
        try:
            init_database()
        except Exception as exc:
            log.critical("Database init failed: %s", exc, exc_info=True)
            sys.exit(1)

        # ── Resolve active user for theme loading ──
        from services.auth_service import get_active_user
        user = get_active_user()

        # ── Apply theme ──
        if user:
            from database.repositories import SettingsRepository
            saved_theme = SettingsRepository().get(user.id, "theme") or DEFAULT_THEME
            theme_manager.set_theme(saved_theme, self)
        else:
            theme_manager.set_theme(DEFAULT_THEME, self)

        # ── Window sizing (desktop default) ──
        from utils.helpers import is_android
        if not is_android():
            Window.size = (420, 800)
            Window.minimum_width  = 360
            Window.minimum_height = 640

        # ── Build screen manager ──
        sm = ScreenManager(transition=FadeTransition(duration=0.25))

        from views.screens.splash_screen     import SplashScreen
        from views.screens.onboarding_screen import OnboardingScreen
        from views.screens.login_screen      import LoginScreen

        sm.add_widget(SplashScreen())
        sm.add_widget(OnboardingScreen())
        sm.add_widget(LoginScreen())

        sm.current = "splash"

        # Note: Notification/backup tasks are scheduled after login now
        return sm

    def on_new_user(self, user_id: int):
        """Called by OnboardingScreen after profile creation."""
        self._user_id = user_id
        from views.screens.main_screen import MainScreen
        sm = self.root
        if "main" not in [s.name for s in sm.screens]:
            main = MainScreen(user_id=user_id)
            sm.add_widget(main)
        sm.current = "main"
        Clock.schedule_interval(lambda _: self._dispatch_notifications(), 60)
        Clock.schedule_once(lambda _: self._auto_backup(), 2)

    def _dispatch_notifications(self):
        if self._user_id:
            try:
                from services.notification_service import dispatch_pending
                dispatch_pending(self._user_id)
            except Exception as exc:
                log.warning("Notification dispatch error: %s", exc)

    def _auto_backup(self):
        try:
            from database.repositories import SettingsRepository
            if self._user_id:
                auto = SettingsRepository().get_bool(self._user_id, "auto_backup")
                if auto:
                    from services.backup_service import create_backup
                    create_backup()
                    log.info("Auto-backup created on startup.")
        except Exception as exc:
            log.warning("Auto-backup failed: %s", exc)

    def on_stop(self):
        from database.connection import close_connection
        close_connection()
        log.info("Tasklyn stopped.")


def main():
    log.info("Starting %s v%s", APP_NAME, APP_VERSION)
    TasklynApp().run()


if __name__ == "__main__":
    main()
