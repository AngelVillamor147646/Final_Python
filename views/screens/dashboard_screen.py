"""
Tasklyn — Dashboard Screen
============================
Main home screen showing all key metrics in a beautiful card layout.
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
from kivymd.uix.button import MDIconButton, MDRaisedButton
from views.widgets import StatCard, TaskCard, BadgeChip, ProgressRing

Builder.load_string("""
<DashboardScreen>:
    name: 'dashboard'
    MDBoxLayout:
        orientation: 'vertical'

        MDTopAppBar:
            id: top_bar
            title: 'Dashboard'
            elevation: 0
            right_action_items: [['bell-outline', lambda x: root.open_notifications()], ['cog-outline', lambda x: root.go_settings()]]

        MDScrollView:
            MDBoxLayout:
                id: content_box
                orientation: 'vertical'
                padding: dp(16)
                spacing: dp(16)
                size_hint_y: None
                height: self.minimum_height
""")


class DashboardScreen(MDScreen):
    def __init__(self, user_id: int, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        Clock.schedule_once(self._build_ui)

    def on_enter(self):
        self._refresh()

    def _build_ui(self, *_):
        box = self.ids.content_box
        box.clear_widgets()
        self._add_greeting(box)
        self._add_stats_row(box)
        self._add_today_tasks(box)
        self._add_today_schedule(box)
        self._add_pomodoro_card(box)
        self._add_streak_card(box)
        self._add_badges_row(box)
        self._add_quick_actions(box)

    def _add_greeting(self, box):
        from services.auth_service import get_active_user
        from utils.date_utils import now
        user = get_active_user()
        h = now().hour
        greeting = "Good morning" if h < 12 else ("Good afternoon" if h < 17 else "Good evening")
        name = user.name if user else "Student"
        lbl = MDLabel(
            text=f"[b]{greeting}, {name}![/b]",
            markup=True, font_style="H6",
            size_hint_y=None, height=dp(40),
        )
        box.add_widget(lbl)

    def _add_stats_row(self, box):
        from services.gamification_service import get_today_accountability
        from services.streak_service import get_current_streak
        from services.pomodoro_service import get_today_summary
        from services.task_service import get_today_tasks

        acc   = round(get_today_accountability(self.user_id))
        streak = get_current_streak(self.user_id)
        pomo  = get_today_summary(self.user_id)
        tasks = get_today_tasks(self.user_id)

        row = MDBoxLayout(orientation="horizontal", spacing=dp(10),
                          size_hint_y=None, height=dp(95))
        row.add_widget(StatCard(icon="shield-star", title="Score",
                                value=f"{acc}%", accent_color=[0.49,0.30,1,1]))
        row.add_widget(StatCard(icon="fire", title="Streak",
                                value=f"{streak}d", accent_color=[1,0.7,0,1]))
        row.add_widget(StatCard(icon="timer", title="Sessions",
                                value=str(pomo["sessions"]), accent_color=[0.26,0.78,0.85,1]))
        row.add_widget(StatCard(icon="check-circle", title="Tasks",
                                value=str(len(tasks)), accent_color=[0.4,0.74,0.42,1]))
        box.add_widget(row)

    def _add_today_tasks(self, box):
        from services.task_service import get_today_tasks, get_overdue_tasks
        header = self._section_header("Today's Tasks", "plus-circle",
                                      lambda: self._nav("tasks"))
        box.add_widget(header)

        tasks = get_today_tasks(self.user_id)[:5]
        overdues = get_overdue_tasks(self.user_id)[:3]
        all_tasks = tasks + overdues

        if not all_tasks:
            box.add_widget(self._empty_label("No tasks due today"))
        else:
            for t in all_tasks:
                card = TaskCard(
                    task_id=t.id, title=t.title,
                    priority=t.priority,
                    deadline=t.deadline[:10] if t.deadline else "",
                    label_color=t.label_color,
                    is_done=(t.status == "done"),
                )
                card.on_complete_callback = self._complete_task
                card.on_tap_callback = lambda tid: self._nav("tasks")
                box.add_widget(card)

    def _add_today_schedule(self, box):
        from services.schedule_service import get_today_classes
        header = self._section_header("Today's Classes", "calendar-today",
                                      lambda: self._nav("schedule"))
        box.add_widget(header)
        classes = get_today_classes(self.user_id)
        if not classes:
            box.add_widget(self._empty_label("No classes scheduled today"))
        else:
            for sc in classes[:4]:
                card = self._schedule_chip(sc)
                box.add_widget(card)

    def _add_pomodoro_card(self, box):
        from services.pomodoro_service import get_today_summary
        pomo = get_today_summary(self.user_id)
        card = MDCard(orientation="horizontal", padding=[dp(14), dp(12)],
                      spacing=dp(12), size_hint_y=None, height=dp(90),
                      elevation=3, radius=[dp(16)])
        ring = ProgressRing(size_hint=(None, None), size=(dp(70), dp(70)))
        sessions = pomo["sessions"]
        ring.progress = min(sessions / 8, 1.0)
        card.add_widget(ring)

        col = MDBoxLayout(orientation="vertical", spacing=dp(4))
        col.add_widget(MDLabel(text="[b]Pomodoro Today[/b]", markup=True,
                               font_style="Subtitle1"))
        col.add_widget(MDLabel(text=f"{sessions} sessions  •  {pomo['total_display']}",
                               theme_text_color="Secondary", font_style="Body2"))
        col.add_widget(MDRaisedButton(text="START TIMER", size_hint_y=None,
                                      height=dp(32),
                                      on_release=lambda *_: self._nav("pomodoro")))
        card.add_widget(col)
        box.add_widget(card)

    def _add_streak_card(self, box):
        from services.streak_service import get_streak_summary
        s = get_streak_summary(self.user_id)
        card = MDCard(orientation="horizontal", padding=[dp(14), dp(12)],
                      spacing=dp(20), size_hint_y=None, height=dp(80),
                      elevation=2, radius=[dp(14)])
        for label, val in [("Current", f"{s['current']} days"),
                            ("Longest", f"{s['longest']} days"),
                            ("Total", f"{s['total_days']} days")]:
            col = MDBoxLayout(orientation="vertical", spacing=dp(2))
            col.add_widget(MDLabel(text=label, font_style="Caption",
                                   theme_text_color="Secondary"))
            col.add_widget(MDLabel(text=val, font_style="Subtitle1", bold=True))
            card.add_widget(col)
        box.add_widget(card)

    def _add_badges_row(self, box):
        from services.gamification_service import get_recent_badges
        header = self._section_header("Recent Badges", "medal",
                                      lambda: self._nav("badges"))
        box.add_widget(header)
        badges = get_recent_badges(self.user_id, limit=5)
        if not badges:
            box.add_widget(self._empty_label("Complete tasks to earn badges!"))
        else:
            row = MDBoxLayout(orientation="horizontal", spacing=dp(8),
                              size_hint_y=None, height=dp(50))
            for b in badges:
                row.add_widget(BadgeChip(badge_icon=b.icon, badge_name=b.name,
                                         is_unlocked=True))
            box.add_widget(row)

    def _add_quick_actions(self, box):
        header = self._section_header("Quick Actions", "lightning-bolt", None)
        box.add_widget(header)
        row = MDBoxLayout(orientation="horizontal", spacing=dp(10),
                          size_hint_y=None, height=dp(50))
        btns = [
            ("Add Task", "plus", "tasks"),
            ("Pomodoro", "timer", "pomodoro"),
            ("Flashcards", "cards", "flashcards"),
            ("Stats", "chart-bar", "statistics"),
        ]
        for label, icon, dest in btns:
            btn = MDRaisedButton(
                text=label, size_hint_x=1, height=dp(44),
                on_release=lambda *_, d=dest: self._nav(d),
            )
            row.add_widget(btn)
        box.add_widget(row)

    # ── helpers ──────────────────────────────────────────────────────────────

    def _section_header(self, title: str, icon: str, on_more) -> MDBoxLayout:
        row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(36))
        row.add_widget(MDLabel(text=f"[b]{title}[/b]", markup=True,
                               font_style="Subtitle1"))
        if on_more:
            btn = MDIconButton(icon="chevron-right", icon_size="20sp",
                               size_hint=(None, None), size=(dp(30), dp(30)),
                               on_release=lambda *_: on_more())
            row.add_widget(btn)
        return row

    def _empty_label(self, text: str) -> MDLabel:
        return MDLabel(text=text, theme_text_color="Hint",
                       halign="center", font_style="Body2",
                       size_hint_y=None, height=dp(36))

    def _schedule_chip(self, sc) -> MDCard:
        card = MDCard(orientation="horizontal", padding=[dp(10), dp(8)],
                      spacing=dp(10), size_hint_y=None, height=dp(50),
                      elevation=1, radius=[dp(10)])
        col = MDBoxLayout(orientation="vertical")
        col.add_widget(MDLabel(text=f"[b]{sc.title}[/b]", markup=True,
                               font_style="Body2"))
        col.add_widget(MDLabel(text=f"{sc.start_time} – {sc.end_time}  {sc.room}",
                               font_style="Caption", theme_text_color="Secondary"))
        card.add_widget(col)
        return card

    def _complete_task(self, task_id: int):
        from services.task_service import complete_task
        ok, badges = complete_task(task_id, self.user_id)
        if ok:
            from utils.helpers import TasklynSnackbar as Snackbar
            Snackbar(text="✅ Task completed!").open()
            if badges:
                Clock.schedule_once(
                    lambda *_: Snackbar(text=f"🏅 Badge unlocked: {badges[0]}").open(), 1
                )
            self._refresh()

    def _nav(self, dest: str):
        from kivymd.app import MDApp
        main_screen = MDApp.get_running_app().root.get_screen("main")
        if dest in ["dashboard", "tasks", "schedule", "pomodoro", "flashcards"]:
            main_screen.switch_tab(dest)
        else:
            main_screen._navigate_to(dest)

    def _refresh(self):
        Clock.schedule_once(self._build_ui, 0)

    def open_notifications(self):
        from services.notification_service import dispatch_pending
        count = dispatch_pending(self.user_id)
        from utils.helpers import TasklynSnackbar as Snackbar
        Snackbar(text=f"{count} notification(s) sent." if count else "No pending notifications.").open()

    def go_settings(self):
        self._nav("settings")
