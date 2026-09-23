"""
Tasklyn — Main Application Screen (bottom navigation shell)
=============================================================
Houses all feature screens inside a KivyMD MDBottomNavigation.
"""
from __future__ import annotations
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.bottomnavigation import MDBottomNavigation, MDBottomNavigationItem

Builder.load_string("""
<MainScreen>:
    name: 'main'
    MDBottomNavigation:
        id: nav
        panel_color: app.theme_cls.bg_dark if app.theme_cls.theme_style == 'Dark' else app.theme_cls.bg_light
        selected_color_background: app.theme_cls.primary_color
        text_color_active: app.theme_cls.primary_color

        MDBottomNavigationItem:
            id: dashboard
            name: 'dashboard'
            text: 'Home'
            icon: 'home-variant'
            on_tab_press: root.on_tab_press('dashboard')

        MDBottomNavigationItem:
            id: tasks
            name: 'tasks'
            text: 'Tasks'
            icon: 'checkbox-marked-circle-outline'
            on_tab_press: root.on_tab_press('tasks')

        MDBottomNavigationItem:
            id: schedule
            name: 'schedule'
            text: 'Schedule'
            icon: 'calendar-month'
            on_tab_press: root.on_tab_press('schedule')

        MDBottomNavigationItem:
            id: pomodoro
            name: 'pomodoro'
            text: 'Focus'
            icon: 'timer-outline'
            on_tab_press: root.on_tab_press('pomodoro')

        MDBottomNavigationItem:
            id: flashcards
            name: 'flashcards'
            text: 'Cards'
            icon: 'cards-outline'
            on_tab_press: root.on_tab_press('flashcards')

        MDBottomNavigationItem:
            name: 'more'
            text: 'More'
            icon: 'dots-horizontal-circle-outline'
            on_tab_press: root.on_tab_press('more')
""")


class MainScreen(MDScreen):
    def __init__(self, user_id: int, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self._screens: dict[str, MDScreen] = {}
        self._current_tab = "dashboard"
        Clock.schedule_once(self._init_screens)

    def _init_screens(self, *_):
        from views.screens.dashboard_screen  import DashboardScreen
        from views.screens.task_screen       import TaskScreen
        from views.screens.schedule_screen   import ScheduleScreen
        from views.screens.pomodoro_screen   import PomodoroScreen
        from views.screens.flashcard_screen  import FlashcardScreen
        from views.screens.statistics_screen import StatisticsScreen
        from views.screens.badges_screen     import BadgesScreen
        from views.screens.skills_screen     import SkillsScreen
        from views.screens.reflection_screen import ReflectionScreen
        from views.screens.settings_screen   import SettingsScreen

        uid = self.user_id
        self._screens = {
            "dashboard":  DashboardScreen(user_id=uid),
            "tasks":      TaskScreen(user_id=uid),
            "schedule":   ScheduleScreen(user_id=uid),
            "pomodoro":   PomodoroScreen(user_id=uid),
            "flashcards": FlashcardScreen(user_id=uid),
            "statistics": StatisticsScreen(user_id=uid),
            "badges":     BadgesScreen(user_id=uid),
            "skills":     SkillsScreen(user_id=uid),
            "reflection": ReflectionScreen(user_id=uid),
            "settings":   SettingsScreen(user_id=uid),
        }
        # The bottom nav items contain their own content area — we embed a
        # ScreenManager per tab item, or just swap content. For simplicity,
        # each tab item hosts the corresponding screen directly.
        nav = self.ids.nav
        tab_map = {
            "dashboard":  self.ids.dashboard,
            "tasks":      self.ids.tasks,
            "schedule":   self.ids.schedule,
            "pomodoro":   self.ids.pomodoro,
            "flashcards": self.ids.flashcards,
        }
        for tab_name, tab_widget in tab_map.items():
            tab_widget.add_widget(self._screens[tab_name])

    def on_tab_press(self, tab_name: str):
        self._current_tab = tab_name
        if tab_name == "more":
            self._show_more_menu()
        else:
            screen = self._screens.get(tab_name)
            if screen and hasattr(screen, "on_enter"):
                screen.on_enter()

    def switch_tab(self, tab_name: str):
        """Programmatically switch the active bottom nav tab."""
        try:
            self.ids.nav.switch_tab(tab_name)
        except Exception:
            pass

    def _show_more_menu(self):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton, MDRaisedButton
        from kivy.uix.boxlayout import BoxLayout
        from kivy.metrics import dp

        content = BoxLayout(orientation="vertical", spacing=dp(8),
                             size_hint_y=None, height=dp(240))
        items = [
            ("Statistics",   "statistics"),
            ("Badges",       "badges"),
            ("Skills",       "skills"),
            ("Reflection",   "reflection"),
            ("Settings",     "settings"),
        ]
        dlg = MDDialog(title="More", type="custom", content_cls=content, buttons=[
            MDFlatButton(text="CLOSE", on_release=lambda *_: dlg.dismiss()),
        ])
        for label, dest in items:
            btn = MDRaisedButton(
                text=label, size_hint_x=1, height=dp(40),
                on_release=lambda *_, d=dest, dl=dlg: (dl.dismiss(),
                                                        self._navigate_to(d)),
            )
            content.add_widget(btn)
        dlg.open()

    def _navigate_to(self, dest: str):
        """Push a feature screen that isn't in the bottom nav."""
        screen = self._screens.get(dest)
        if screen:
            # Use the root ScreenManager
            sm = self.manager
            if dest not in [s.name for s in sm.screens]:
                sm.add_widget(screen)
            sm.current = dest
            if hasattr(screen, "on_enter"):
                screen.on_enter()
