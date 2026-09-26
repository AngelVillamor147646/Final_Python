"""
Tasklyn — Statistics Screen
==============================
Charts: study hours, task completion, flashcard accuracy, subject breakdown.
"""
from __future__ import annotations
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from utils.helpers import TasklynSnackbar as Snackbar
from views.widgets import ChartImage, StatCard

Builder.load_string("""
<StatisticsScreen>:
    name: 'statistics'
    MDBoxLayout:
        orientation: 'vertical'

        MDTopAppBar:
            title: 'Statistics'
            elevation: 0
            left_action_items: [["arrow-left", lambda x: setattr(root.manager, 'current', 'main')]]
            right_action_items: [['file-pdf-box', lambda x: root.export_pdf()], ['file-delimited', lambda x: root.export_csv()]]

        MDBoxLayout:
            id: range_row
            orientation: 'horizontal'
            size_hint_y: None
            height: dp(44)
            padding: dp(8), 0
            spacing: dp(8)

        MDScrollView:
            MDBoxLayout:
                id: content
                orientation: 'vertical'
                padding: dp(12)
                spacing: dp(16)
                size_hint_y: None
                height: self.minimum_height
""")


class StatisticsScreen(MDScreen):
    def __init__(self, user_id: int, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self._range = "week"
        Clock.schedule_once(self._build_range_tabs)

    def on_enter(self):
        Clock.schedule_once(self._build_charts, 0.1)

    def _build_range_tabs(self, *_):
        row = self.ids.range_row
        row.clear_widgets()
        for label, key in [("Week", "week"), ("Month", "month"), ("Year", "year")]:
            btn = MDRaisedButton(text=label, size_hint_x=1, height=dp(36),
                                  on_release=lambda *_, k=key: self._set_range(k))
            if key == self._range:
                btn.md_bg_color = [0.49, 0.30, 1, 1]
            row.add_widget(btn)

    def _set_range(self, key: str):
        self._range = key
        self._build_range_tabs()
        Clock.schedule_once(self._build_charts, 0.1)

    def _build_charts(self, *_):
        from services.statistics_service import get_analytics_dashboard_stats
        from statistics.chart_builder import dual_bar_chart_png

        stats = get_analytics_dashboard_stats(self.user_id)

        box = self.ids.content
        box.clear_widgets()

        # ── KPI row 1 ──
        kpi_row1 = MDBoxLayout(orientation="horizontal", spacing=dp(8),
                               size_hint_y=None, height=dp(95))
        kpi_row1.add_widget(StatCard(icon="check-circle", title="Done Today",
                                     value=str(stats["tasks_completed_today"]),
                                     accent_color=[0.3,0.7,0.3,1]))
        kpi_row1.add_widget(StatCard(icon="check-all", title="Done Week",
                                     value=str(stats["tasks_completed_week"]),
                                     accent_color=[0.49,0.30,1,1]))
        kpi_row1.add_widget(StatCard(icon="timer", title="Pomo Hrs",
                                     value=str(stats["pomodoro_hours_today"]),
                                     accent_color=[1,0.6,0,1]))
        box.add_widget(kpi_row1)
        
        # ── KPI row 2 ──
        kpi_row2 = MDBoxLayout(orientation="horizontal", spacing=dp(8),
                               size_hint_y=None, height=dp(95))
        kpi_row2.add_widget(StatCard(icon="calendar-star", title="Best Day",
                                     value=stats["most_productive_day"],
                                     accent_color=[1,0.38,0.38,1]))
        kpi_row2.add_widget(StatCard(icon="star", title="Habits",
                                     value=str(stats["total_habits"]),
                                     accent_color=[0.2,0.8,0.8,1]))
        kpi_row2.add_widget(MDBoxLayout()) # spacer
        box.add_widget(kpi_row2)

        # ── Tasks Done vs Overdue bar chart ──
        chart_data = stats.get("chart_data", [])
        if chart_data:
            labels = [d["day"] for d in chart_data]
            done_vals = [d["done"] for d in chart_data]
            overdue_vals = [d["overdue"] for d in chart_data]
            png = dual_bar_chart_png(labels, done_vals, overdue_vals, title="Tasks: Done vs Overdue")
            box.add_widget(MDLabel(text="[b]Weekly Performance[/b]", markup=True,
                                   font_style="Subtitle2", size_hint_y=None, height=dp(28)))
            ci = ChartImage(png_bytes=png, size_hint_y=None, height=dp(250))
            box.add_widget(ci)

    def export_pdf(self):
        from services.backup_service import export_stats_pdf
        ok, msg, path = export_stats_pdf(self.user_id)
        Snackbar(text=msg).open()

    def export_csv(self):
        from services.backup_service import export_tasks_csv
        path = export_tasks_csv(self.user_id)
        Snackbar(text=f"Exported to {path.name}").open()
