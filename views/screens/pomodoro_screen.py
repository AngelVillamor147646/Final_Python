"""
Tasklyn — Pomodoro Timer Screen
================================
Animated circular ring timer with work/break cycles, session logging, notifications.
"""
from __future__ import annotations
import math
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.animation import Animation
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.card import MDCard
from utils.helpers import TasklynSnackbar as Snackbar
from views.widgets import ProgressRing

Builder.load_string("""
<PomodoroScreen>:
    name: 'pomodoro'
    MDBoxLayout:
        orientation: 'vertical'

        MDTopAppBar:
            title: 'Pomodoro Timer'
            elevation: 0
            right_action_items: [['history', lambda x: root.show_history()], ['cog', lambda x: root.show_settings()]]

        MDScrollView:
            MDBoxLayout:
                id: content
                orientation: 'vertical'
                padding: dp(20)
                spacing: dp(20)
                size_hint_y: None
                height: self.minimum_height
""")


class PomodoroScreen(MDScreen):
    # Timer states
    IDLE      = "idle"
    WORKING   = "working"
    BREAK     = "break"
    LONG_BREAK = "long_break"

    def __init__(self, user_id: int, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self._state   = self.IDLE
        self._seconds_left = 0
        self._total_seconds = 0
        self._session_id   = None
        self._session_count = 0
        self._tick_event   = None
        self._interruptions = 0
        self._work_min  = 25
        self._break_min = 5
        self._long_break_min = 15
        Clock.schedule_once(self._build_ui)

    def on_enter(self):
        self._load_settings()

    def _load_settings(self):
        from database.repositories import SettingsRepository
        s = SettingsRepository()
        self._work_min = s.get_int(self.user_id, "pomodoro_work") or 25
        self._break_min = s.get_int(self.user_id, "pomodoro_break") or 5
        self._long_break_min = s.get_int(self.user_id, "pomodoro_long_break") or 15

    def _build_ui(self, *_):
        box = self.ids.content
        box.clear_widgets()
        
        # Timer Card
        timer_card = MDCard(
            orientation="vertical", padding=dp(24), spacing=dp(20),
            size_hint=(0.95, None), height=dp(480), pos_hint={"center_x": .5},
            radius=[dp(24)], elevation=2,
        )
        from kivymd.app import MDApp
        app = MDApp.get_running_app()
        timer_card.md_bg_color = [1, 1, 1, 0.05] if app.theme_cls.theme_style == 'Dark' else [0, 0, 0, 0.02]

        # Mode label
        self._mode_lbl = MDLabel(text="FOCUS TIME", font_style="Overline",
                                  halign="center", theme_text_color="Secondary",
                                  size_hint_y=None, height=dp(24))
        timer_card.add_widget(self._mode_lbl)

        # Ring + time label
        ring_wrapper = MDBoxLayout(orientation="vertical",
                                    size_hint_y=None, height=dp(220),
                                    pos_hint={"center_x": .5})
        self._ring = ProgressRing(size_hint=(None, None), size=(dp(200), dp(200)),
                                   pos_hint={"center_x": .5})
        self._ring.progress = 1.0
        ring_wrapper.add_widget(self._ring)

        # Overlaid time text
        self._time_lbl = MDLabel(
            text=self._fmt_time(self._work_min * 60),
            font_style="H3", bold=True, halign="center",
            theme_text_color="Primary",
            size_hint_y=None, height=dp(50),
        )
        timer_card.add_widget(self._time_lbl)
        timer_card.add_widget(ring_wrapper)

        # Session counter
        self._session_lbl = MDLabel(
            text="Session 0 / 4", halign="center",
            theme_text_color="Secondary", font_style="Body2",
            size_hint_y=None, height=dp(24),
        )
        timer_card.add_widget(self._session_lbl)
        
        # Adjust Time row
        adj_row = MDBoxLayout(orientation="horizontal", spacing=dp(30),
                              size_hint_y=None, height=dp(40),
                              adaptive_width=True, pos_hint={"center_x": .5})
        adj_row.add_widget(MDIconButton(icon="minus", icon_size="24sp", theme_icon_color="Custom", icon_color=[0.7,0.7,0.7,1], on_release=lambda x: self._adjust_time(-60)))
        adj_row.add_widget(MDIconButton(icon="plus", icon_size="24sp", theme_icon_color="Custom", icon_color=[0.7,0.7,0.7,1], on_release=lambda x: self._adjust_time(60)))
        timer_card.add_widget(adj_row)

        # Buttons
        btn_row = MDBoxLayout(orientation="horizontal", spacing=dp(16),
                               size_hint_y=None, height=dp(50),
                               adaptive_width=True, pos_hint={"center_x": .5})
        self._start_btn = MDRaisedButton(text="START", height=dp(44), on_release=self._start)
        self._pause_btn = MDFlatButton(text="PAUSE", height=dp(44),
                                       on_release=self._pause, disabled=True)
        self._stop_btn  = MDFlatButton(text="STOP", height=dp(44), text_color=[1,0.3,0.3,1],
                                        on_release=self._stop,  disabled=True)
        for b in [self._start_btn, self._pause_btn, self._stop_btn]:
            btn_row.add_widget(b)
        timer_card.add_widget(btn_row)
        
        box.add_widget(timer_card)

        # Today's summary
        self._summary_lbl = MDLabel(
            text=self._get_summary_text(), halign="center",
            theme_text_color="Secondary", font_style="Caption",
            size_hint_y=None, height=dp(40),
        )
        box.add_widget(self._summary_lbl)

    # ── Timer control ──────────────────────────────────────────────────────

    def _adjust_time(self, seconds: int):
        self._seconds_left += seconds
        if self._seconds_left < 60:
            self._seconds_left = 60
            
        if self._state == self.IDLE:
            self._total_seconds = self._seconds_left
        
        if self._total_seconds < self._seconds_left:
             self._total_seconds = self._seconds_left

        self._ring.progress = self._seconds_left / max(self._total_seconds, 1)
        self._time_lbl.text = self._fmt_time(self._seconds_left)

    def _start(self, *_):
        if self._state == self.IDLE:
            self._session_count = 0
            self._start_work()
        elif self._state in (self.BREAK, self.LONG_BREAK):
            self._start_work()
        else:
            # Resume from pause
            self._tick_event = Clock.schedule_interval(self._tick, 1)
            self._pause_btn.disabled = False
            self._start_btn.disabled = True

    def _start_work(self):
        from services.pomodoro_service import start_session
        self._session = start_session(self.user_id, self._work_min, self._break_min)
        self._session_id = self._session.id
        self._total_seconds = self._work_min * 60
        self._seconds_left  = self._total_seconds
        self._state = self.WORKING
        self._interruptions = 0
        self._mode_lbl.text = "FOCUS TIME"
        self._ring.fill_color = [0.49, 0.30, 1.0, 1]
        self._start_btn.disabled = True
        self._pause_btn.disabled = False
        self._stop_btn.disabled  = False
        self._session_lbl.text = f"Session {self._session_count + 1} / 4"
        if self._tick_event:
            self._tick_event.cancel()
        self._tick_event = Clock.schedule_interval(self._tick, 1)

    def _start_break(self, long: bool = False):
        self._session_count += 1
        mins = self._long_break_min if long else self._break_min
        self._total_seconds = mins * 60
        self._seconds_left  = self._total_seconds
        self._state = self.LONG_BREAK if long else self.BREAK
        label = "LONG BREAK" if long else "SHORT BREAK"
        self._mode_lbl.text = label
        self._ring.fill_color = [1, 0.7, 0, 1]
        self._start_btn.disabled = False
        self._start_btn.text = "NEXT"

    def _pause(self, *_):
        if self._tick_event:
            self._tick_event.cancel()
            self._tick_event = None
        self._interruptions += 1
        self._pause_btn.disabled = True
        self._start_btn.disabled = False
        self._start_btn.text = "RESUME"

    def _stop(self, *_):
        if self._tick_event:
            self._tick_event.cancel()
            self._tick_event = None
        if self._session_id and self._state == self.WORKING:
            from services.pomodoro_service import abandon_session
            abandon_session(self._session_id)
        self._state = self.IDLE
        self._session_id = None
        self._seconds_left = self._work_min * 60
        self._total_seconds = self._work_min * 60
        self._ring.progress = 1.0
        self._time_lbl.text = self._fmt_time(self._seconds_left)
        self._mode_lbl.text = "FOCUS TIME"
        self._ring.fill_color = [0.49, 0.30, 1.0, 1]
        self._start_btn.disabled = False
        self._start_btn.text = "START"
        self._pause_btn.disabled = True
        self._stop_btn.disabled  = True
        self._summary_lbl.text = self._get_summary_text()

    def _tick(self, dt: float):
        self._seconds_left -= 1
        self._ring.progress = self._seconds_left / max(self._total_seconds, 1)
        self._time_lbl.text = self._fmt_time(self._seconds_left)
        if self._seconds_left <= 0:
            self._on_timer_end()

    def _on_timer_end(self):
        if self._tick_event:
            self._tick_event.cancel()
        if self._state == self.WORKING:
            # Complete session
            from services.pomodoro_service import complete_session
            badges = complete_session(self._session_id, self.user_id, self._interruptions)
            from services.notification_service import send_pomodoro_notification
            send_pomodoro_notification("work")
            Snackbar(text="🍅 Session complete! Take a break.").open()
            if badges:
                Clock.schedule_once(
                    lambda *_: Snackbar(text=f"🏅 {badges[0]}").open(), 1.5)
            long = (self._session_count + 1) % 4 == 0
            self._start_break(long=long)
        else:
            from services.notification_service import send_pomodoro_notification
            send_pomodoro_notification("break")
            Snackbar(text="⏰ Break over! Ready to focus?").open()
            self._state = self.IDLE
            self._seconds_left = self._work_min * 60
            self._total_seconds = self._work_min * 60
            self._ring.progress = 1.0
            self._time_lbl.text = self._fmt_time(self._seconds_left)
            self._start_btn.disabled = False
            self._start_btn.text = "START"
            self._stop_btn.disabled = True
        self._summary_lbl.text = self._get_summary_text()

    # ── Helpers ───────────────────────────────────────────────────────────

    @staticmethod
    def _fmt_time(seconds: int) -> str:
        m, s = divmod(max(0, seconds), 60)
        return f"{m:02d}:{s:02d}"

    def _get_summary_text(self) -> str:
        from services.pomodoro_service import get_today_summary
        s = get_today_summary(self.user_id)
        return f"Today: {s['sessions']} sessions  •  {s['total_display']} studied"

    def show_history(self):
        from services.pomodoro_service import get_history
        sessions = get_history(self.user_id, limit=20)
        lines = "\n".join(
            f"{'✅' if s.completed else '❌'} {s.started_at[:16]}  {s.work_minutes}min"
            for s in sessions[:10]
        )
        from kivymd.uix.dialog import MDDialog
        dlg = MDDialog(
            title="Recent Sessions",
            text=lines or "No sessions yet.",
            buttons=[MDFlatButton(text="CLOSE", on_release=lambda *_: dlg.dismiss())],
        )
        dlg.open()

    def show_settings(self):
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.textfield import MDTextField
        content = MDBoxLayout(orientation="vertical", spacing=dp(8),
                               size_hint_y=None, height=dp(200), padding=[dp(4)]*4)
        self._pw = MDTextField(hint_text="Work minutes", text=str(self._work_min))
        self._pb = MDTextField(hint_text="Break minutes", text=str(self._break_min))
        self._pl = MDTextField(hint_text="Long break minutes", text=str(self._long_break_min))
        for w in [self._pw, self._pb, self._pl]:
            content.add_widget(w)
            
        self._settings_dlg = MDDialog(
            title="Timer Settings", type="custom", content_cls=content,
        )
        self._settings_dlg.buttons = [
            MDFlatButton(text="CANCEL", on_release=lambda *_: self._settings_dlg.dismiss()),
            MDRaisedButton(text="SAVE",  on_release=self._save_settings),
        ]
        self._settings_dlg.open()

    def _save_settings(self, *_):
        from database.repositories import SettingsRepository
        s = SettingsRepository()
        try:
            self._work_min       = max(1, int(self._pw.text))
            self._break_min      = max(1, int(self._pb.text))
            self._long_break_min = max(1, int(self._pl.text))
        except ValueError:
            pass
        s.set(self.user_id, "pomodoro_work",       str(self._work_min))
        s.set(self.user_id, "pomodoro_break",      str(self._break_min))
        s.set(self.user_id, "pomodoro_long_break", str(self._long_break_min))
        
        if hasattr(self, '_settings_dlg'):
            self._settings_dlg.dismiss()
            
        Snackbar(text="Timer settings saved.").open()
