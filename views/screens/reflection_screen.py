"""
Tasklyn — Reflection Screen
==============================
Weekly summary: study hours, tasks, badges earned, improvement suggestions.
"""
from __future__ import annotations
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard

Builder.load_string("""
<ReflectionScreen>:
    name: 'reflection'
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: 'Weekly Reflection'
            elevation: 0
            left_action_items: [["arrow-left", lambda x: setattr(root.manager, 'current', 'main')]]
        MDScrollView:
            MDBoxLayout:
                id: content
                orientation: 'vertical'
                padding: dp(16)
                spacing: dp(14)
                size_hint_y: None
                height: self.minimum_height
""")

# Rule-based suggestion engine
_SUGGESTIONS = {
    "low_study":       ("book-open-variant", "Try to study at least 1 hour per day — consistency beats intensity!"),
    "many_late":       ("clock-alert", "Several tasks were late this week. Try breaking them into smaller chunks."),
    "low_accuracy":    ("brain", "Your flashcard accuracy is below 60%. Review missed cards more often."),
    "no_pomodoro":     ("timer-off", "You haven't used the Pomodoro timer yet. Give it a try to boost focus!"),
    "great_streak":    ("fire", "Amazing streak! Keep it up — you're building great habits."),
    "perfect_score":   ("star-circle", "Excellent accountability score! You're crushing your academic goals."),
    "low_streak":      ("calendar-remove", "Start small: complete at least one task per day to build your streak."),
    "all_done":        ("check-all", "All tasks completed on time this week — outstanding discipline!"),
}


class ReflectionScreen(MDScreen):
    def __init__(self, user_id: int, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        Clock.schedule_once(self._build)

    def on_enter(self):
        self._build()

    def _build(self, *_):
        from services.statistics_service import get_weekly_stats
        from services.streak_service import get_streak_summary
        from services.gamification_service import get_recent_badges, get_today_accountability
        from utils.date_utils import start_of_week, end_of_week, fmt_date
        from kivymd.uix.gridlayout import MDGridLayout
        from kivymd.uix.label import MDIcon
        from views.widgets import StatCard

        stats  = get_weekly_stats(self.user_id)
        streak = get_streak_summary(self.user_id)
        badges = get_recent_badges(self.user_id, limit=10)
        acc    = get_today_accountability(self.user_id)

        box = self.ids.content
        box.clear_widgets()

        # Header
        from utils.date_utils import display_date, start_of_week, end_of_week
        s = display_date(start_of_week()); e = display_date(end_of_week())
        box.add_widget(MDLabel(
            text=f"[b]Week of {s} – {e}[/b]", markup=True,
            font_style="H6", size_hint_y=None, height=dp(44),
        ))

        # KPI cards in a 2-column grid
        kpis = [
            ("book", "Study Time",    f"{stats['study_minutes']//60}h {stats['study_minutes']%60}m", [0.49, 0.30, 1, 1]),
            ("check-circle", "Tasks Done",    str(stats["tasks_completed"]), [0.4, 0.74, 0.42, 1]),
            ("close-circle", "Late Tasks",    str(stats["tasks_late"]), [0.85, 0.3, 0.3, 1]),
            ("timer", "Sessions",     str(stats["pomodoro_sessions"]), [0.26, 0.78, 0.85, 1]),
            ("target", "FC Accuracy",  f"{stats['flashcard_accuracy']}%", [0.9, 0.5, 0.1, 1]),
            ("fire", "Current Streak", f"{streak['current']} days", [1, 0.7, 0, 1]),
            ("chart-bar", "Acc. Score",   f"{round(acc)}%", [0.49, 0.30, 1, 1]),
        ]
        
        grid = MDGridLayout(cols=2, spacing=dp(12), size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        for icon, title, val, color in kpis:
            card = StatCard(icon=icon, title=title, value=val, accent_color=color)
            grid.add_widget(card)
        box.add_widget(grid)

        # Badges this week
        if badges:
            box.add_widget(MDLabel(text="[b]Badges Earned[/b]", markup=True,
                                   font_style="Subtitle2", size_hint_y=None, height=dp(28)))
            names = "  •  ".join(b.name for b in badges[:5])
            box.add_widget(MDLabel(text=names, theme_text_color="Secondary",
                                   font_style="Body2", size_hint_y=None, height=dp(28)))

        # Suggestions
        suggestions = self._generate_suggestions(stats, streak, acc)
        if suggestions:
            box.add_widget(MDLabel(text="[b]Improvement Suggestions[/b]", markup=True,
                                   font_style="Subtitle2", size_hint_y=None, height=dp(32)))
            for icon, text in suggestions:
                card = MDCard(orientation="horizontal", padding=[dp(16), dp(8)],
                              spacing=dp(16), size_hint_y=None, height=dp(70),
                              elevation=1, radius=[dp(12)])
                
                icon_lbl = MDIcon(icon=icon, font_size="24sp",
                                  theme_text_color="Primary",
                                  pos_hint={"center_y": .5},
                                  size_hint=(None, None), size=(dp(30), dp(30)))
                card.add_widget(icon_lbl)
                
                txt_lbl = MDLabel(text=text, font_style="Caption",
                                  theme_text_color="Secondary",
                                  valign="center")
                card.add_widget(txt_lbl)
                box.add_widget(card)

    def _generate_suggestions(self, stats: dict, streak: dict, acc: float) -> list[tuple]:
        s = []
        if stats["study_minutes"] < 120:
            s.append(_SUGGESTIONS["low_study"])
        if stats["tasks_late"] >= 3:
            s.append(_SUGGESTIONS["many_late"])
        if stats["flashcard_accuracy"] < 60 and stats["pomodoro_sessions"] > 0:
            s.append(_SUGGESTIONS["low_accuracy"])
        if stats["pomodoro_sessions"] == 0:
            s.append(_SUGGESTIONS["no_pomodoro"])
        if streak["current"] >= 7:
            s.append(_SUGGESTIONS["great_streak"])
        if acc >= 95:
            s.append(_SUGGESTIONS["perfect_score"])
        if streak["current"] == 0:
            s.append(_SUGGESTIONS["low_streak"])
        if stats["tasks_late"] == 0 and stats["tasks_completed"] > 0:
            s.append(_SUGGESTIONS["all_done"])
        return s[:4]  # max 4 suggestions
