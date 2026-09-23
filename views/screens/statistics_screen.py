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
        from services.statistics_service import get_weekly_stats, get_monthly_stats, get_yearly_study_hours
        from utils.date_utils import start_of_week, end_of_week, start_of_month, end_of_month, fmt_date, today
        from statistics.chart_builder import bar_chart_png, line_chart_png, pie_chart_png

        if self._range == "week":
            stats = get_weekly_stats(self.user_id)
        elif self._range == "month":
            stats = get_monthly_stats(self.user_id)
        else:
            stats = get_monthly_stats(self.user_id)  # fallback for year

        box = self.ids.content
        box.clear_widgets()

        # ── KPI row ──
        kpi_row = MDBoxLayout(orientation="horizontal", spacing=dp(8),
                               size_hint_y=None, height=dp(95))
        kpi_row.add_widget(StatCard(icon="check-circle", title="Tasks Done",
                                     value=str(stats["tasks_completed"]),
                                     accent_color=[0.4,0.74,0.42,1]))
        kpi_row.add_widget(StatCard(icon="clock-alert", title="Late",
                                     value=str(stats["tasks_late"]),
                                     accent_color=[1,0.38,0.38,1]))
        kpi_row.add_widget(StatCard(icon="timer", title="Sessions",
                                     value=str(stats["pomodoro_sessions"]),
                                     accent_color=[0.49,0.30,1,1]))
        kpi_row.add_widget(StatCard(icon="head-lightbulb", title="FC Acc.",
                                     value=f"{stats['flashcard_accuracy']}%",
                                     accent_color=[1,0.7,0,1]))
        box.add_widget(kpi_row)

        # ── Study hours bar chart ──
        daily = stats.get("daily_study_minutes", [])
        if daily:
            labels = [d["date"][-5:] for d in daily]
            values = [round(d["minutes"] / 60, 2) for d in daily]
            png = bar_chart_png(labels, values, "Study Hours", "Date", "Hours")
            box.add_widget(MDLabel(text="[b]Daily Study Hours[/b]", markup=True,
                                   font_style="Subtitle2", size_hint_y=None, height=dp(28)))
            ci = ChartImage(png_bytes=png, size_hint_y=None, height=dp(220))
            box.add_widget(ci)

        # ── Subject breakdown pie ──
        subj = stats.get("subject_minutes", [])
        if subj and len(subj) > 1:
            labels = [s["subject"] for s in subj]
            values = [s["minutes"] for s in subj]
            png = pie_chart_png(labels, values, "Study by Subject")
            box.add_widget(MDLabel(text="[b]Study by Subject[/b]", markup=True,
                                   font_style="Subtitle2", size_hint_y=None, height=dp(28)))
            ci = ChartImage(png_bytes=png, size_hint_y=None, height=dp(250))
            box.add_widget(ci)

        # ── Accountability trend ──
        from services.gamification_service import get_accountability_history
        hist = get_accountability_history(self.user_id, days=14)
        if hist:
            dates = [h["date"][-5:] for h in hist]
            scores = [h["score"] for h in hist]
            png = line_chart_png(dates, scores, "Accountability Score", "Score")
            box.add_widget(MDLabel(text="[b]Accountability Trend[/b]", markup=True,
                                   font_style="Subtitle2", size_hint_y=None, height=dp(28)))
            ci = ChartImage(png_bytes=png, size_hint_y=None, height=dp(200))
            box.add_widget(ci)

    def export_pdf(self):
        from services.backup_service import export_stats_pdf
        ok, msg, path = export_stats_pdf(self.user_id)
        Snackbar(text=msg).open()

    def export_csv(self):
        from services.backup_service import export_tasks_csv
        path = export_tasks_csv(self.user_id)
        Snackbar(text=f"Exported to {path.name}").open()
