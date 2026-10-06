"""
Tasklyn — Schedule Manager Screen
=====================================
Weekly timetable grid + daily view with conflict detection.
"""
from __future__ import annotations
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from utils.helpers import TasklynSnackbar as Snackbar
from kivymd.uix.menu import MDDropdownMenu

DAY_NAMES = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

Builder.load_string("""
<ScheduleScreen>:
    name: 'schedule'
    MDBoxLayout:
        orientation: 'vertical'

        MDTopAppBar:
            title: 'Schedule'
            elevation: 0
        MDBoxLayout:
            id: day_tabs
            orientation: 'horizontal'
            size_hint_y: None
            height: dp(50)
            padding: dp(8), dp(4)
            spacing: dp(6)

        MDFloatLayout:
            MDScrollView:
                MDBoxLayout:
                    id: schedule_list
                    orientation: 'vertical'
                    padding: dp(16)
                    spacing: dp(12)
                    size_hint_y: None
                    height: self.minimum_height
            
            MDFloatingActionButton:
                icon: "plus"
                md_bg_color: app.theme_cls.primary_color
                pos_hint: {"right": 0.95, "y": 0.05}
                on_release: root.open_add_dialog()
""")


from datetime import datetime, date, timedelta

class CountdownLabel(MDLabel):
    def __init__(self, target_time_str: str, **kwargs):
        super().__init__(**kwargs)
        self.font_style = "Caption"
        self.theme_text_color = "Primary"
        self.bold = True
        
        # parse HH:MM
        try:
            h, m = map(int, target_time_str.split(':'))
            now = datetime.now()
            # We assume the schedule is for today, if the tab is today
            self.target_dt = now.replace(hour=h, minute=m, second=0, microsecond=0)
            self._update_event = Clock.schedule_interval(self.update_timer, 1)
            self.update_timer()
        except:
            self.text = ""

    def update_timer(self, *_):
        now = datetime.now()
        diff = self.target_dt - now
        if diff.total_seconds() <= 0:
            self.text = "In Progress / Passed"
            if hasattr(self, '_update_event'):
                self._update_event.cancel()
        else:
            s = int(diff.total_seconds())
            h, r = divmod(s, 3600)
            m, sec = divmod(r, 60)
            self.text = f"Starts in: {h}h {m}m {sec}s"

class ScheduleScreen(MDScreen):
    def __init__(self, user_id: int, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self._selected_day = date.today().weekday()
        self._dialog = None
        Clock.schedule_once(self._build_day_tabs)

    def on_enter(self):
        self._refresh()

    def _build_day_tabs(self, *_):
        tabs = self.ids.day_tabs
        tabs.clear_widgets()
        for i, name in enumerate(DAY_NAMES):
            is_sel = (i == self._selected_day)
            btn = MDRaisedButton(
                text=name, size_hint_x=1, size_hint_y=None, height=dp(40),
                elevation=2 if is_sel else 0,
                md_bg_color=[0.49, 0.30, 1, 1] if is_sel else [0.49, 0.30, 1, 0.1],
                text_color=[1, 1, 1, 1] if is_sel else [0.7, 0.7, 0.8, 1],
                on_release=lambda *_, d=i: self._select_day(d),
            )
            tabs.add_widget(btn)

    def _select_day(self, day: int):
        self._selected_day = day
        self._build_day_tabs()
        self._refresh()

    def _refresh(self, *_):
        from services.schedule_service import get_day_schedule
        classes = get_day_schedule(self.user_id, self._selected_day)
        box = self.ids.schedule_list
        box.clear_widgets()
        if not classes:
            box.add_widget(MDLabel(text="No classes on this day.",
                                   halign="center", theme_text_color="Hint",
                                   size_hint_y=None, height=dp(60)))
        for sc in classes:
            card = self._make_card(sc)
            box.add_widget(card)

    def _make_card(self, sc) -> MDCard:
        from utils.helpers import hex_to_kivy_colour
        card = MDCard(orientation="horizontal", padding=[dp(12), dp(10)],
                      spacing=dp(12), size_hint_y=None, height=dp(110),
                      elevation=2, radius=[dp(12)])
        # Colour strip
        from kivy.graphics import Color, RoundedRectangle
        with card.canvas.before:
            Color(*hex_to_kivy_colour(sc.color))
            RoundedRectangle(pos=(card.x, card.y), size=(dp(4), dp(110)),
                             radius=[dp(4)])
        col = MDBoxLayout(orientation="vertical", spacing=dp(2))
        col.add_widget(MDLabel(text=f"[b]{sc.title}[/b]", markup=True,
                               font_style="Subtitle1"))
        
        # Details row
        details = f"{sc.start_time} – {sc.end_time}"
        if sc.room: details += f"  •  Room: {sc.room}"
        if sc.instructor: details += f"  •  By {sc.instructor}"
        col.add_widget(MDLabel(text=details, font_style="Caption",
                               theme_text_color="Secondary"))
                               
        if sc.notes:
            col.add_widget(MDLabel(text=f"Notes: {sc.notes}", font_style="Caption", theme_text_color="Hint"))

        # Add countdown timer if it's today
        import datetime
        if self._selected_day == datetime.date.today().weekday():
            timer = CountdownLabel(sc.start_time)
            col.add_widget(timer)

        card.add_widget(col)
        # Delete button
        del_btn = MDIconButton(icon="delete-outline", icon_size="18sp",
                               size_hint=(None, None), size=(dp(36), dp(36)),
                               on_release=lambda *_, sid=sc.id: self._delete(sid))
        card.add_widget(del_btn)
        return card

    def open_add_dialog(self):
        from services.schedule_service import get_subjects
        subjects = get_subjects(self.user_id)
        
        content = MDBoxLayout(orientation="vertical", spacing=dp(16),
                              size_hint_y=None, padding=dp(8))
        content.bind(minimum_height=content.setter('height'))
        
        from kivymd.uix.selectioncontrol import MDCheckbox
        from kivymd.uix.gridlayout import MDGridLayout
        
        self._s_title  = MDTextField(hint_text="Class title *", text="", mode="fill", radius=[dp(10)])
        self._s_start  = MDTextField(hint_text="Start time", text="", mode="fill", radius=[dp(10)], readonly=True)
        self._s_start.bind(focus=lambda inst, val: self._open_time_picker("start") if val else None)
        self._s_end    = MDTextField(hint_text="End time", text="", mode="fill", radius=[dp(10)], readonly=True)
        self._s_end.bind(focus=lambda inst, val: self._open_time_picker("end") if val else None)
        self._s_room   = MDTextField(hint_text="Room / location", text="", mode="fill", radius=[dp(10)])
        self._s_instr  = MDTextField(hint_text="Instructor", text="", mode="fill", radius=[dp(10)])
        self._s_notes  = MDTextField(hint_text="Notes (optional)", text="", mode="fill", radius=[dp(10)])
        self._s_remind = MDTextField(hint_text="Reminder (minutes before)", text="15", mode="fill", radius=[dp(10)])
        
        for w in [self._s_title, self._s_start, self._s_end,
                  self._s_room, self._s_instr, self._s_notes, self._s_remind]:
            content.add_widget(w)

        content.add_widget(MDLabel(text="Select Days:", font_style="Subtitle2", size_hint_y=None, height=dp(24)))
        days_box = MDGridLayout(cols=3, size_hint_y=None, spacing=dp(4))
        days_box.bind(minimum_height=days_box.setter('height'))
        
        self._day_checks = []
        for i, name in enumerate(["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]):
            row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40))
            cb = MDCheckbox(size_hint=(None, None), size=(dp(40), dp(40)))
            if i == self._selected_day: cb.active = True
            self._day_checks.append((i, cb))
            row.add_widget(cb)
            row.add_widget(MDLabel(text=name))
            days_box.add_widget(row)
            
        content.add_widget(days_box)

        from kivy.core.window import Window
        from kivymd.uix.scrollview import MDScrollView
        scroll = MDScrollView(size_hint_y=None)
        scroll.height = min(dp(500), Window.height - dp(200))
        scroll.add_widget(content)

        self._dialog = MDDialog(
            title="Add Class",
            type="custom", content_cls=scroll,
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda *_: self._dialog.dismiss()),
                MDRaisedButton(text="SAVE",  on_release=self._save),
            ],
        )
        self._dialog.open()

    def _open_time_picker(self, which: str):
        from kivymd.app import MDApp
        from kivymd.uix.pickers import MDTimePicker
        MDApp.get_running_app().theme_cls.device_orientation = "portrait"
        picker = MDTimePicker()
        picker.bind(time=lambda inst, t: self._on_time_picked(which, t))
        picker.open()

    def _on_time_picked(self, which: str, t):
        value = t.strftime("%H:%M")  # stores as 24-hour, e.g. "14:30"
        display = t.strftime("%I:%M %p").lstrip("0")  # shows as "2:30 PM"
        if which == "start":
            self._s_start.text = display
            self._start_value = value
        else:
            self._s_end.text = display
            self._end_value = value

    def _save(self, *_):
        from services.schedule_service import create_schedule
        try:
            remind = int(self._s_remind.text or "15")
        except ValueError:
            remind = 15
            
        selected_days = [day for day, cb in self._day_checks if cb.active]
        if not selected_days:
            Snackbar(text="Select at least one day!", notif_type="warning").open()
            return

        ok, err, sc = create_schedule(
            user_id=self.user_id,
            title=self._s_title.text,
            days=selected_days,
            start_time=getattr(self, "_start_value", ""),
            end_time=getattr(self, "_end_value", ""),
            room=self._s_room.text,
            instructor=self._s_instr.text,
            notes=self._s_notes.text,
            reminder_minutes=remind,
        )

        if ok:
            self._dialog.dismiss()
            self._refresh()
            Snackbar(text="Class added!", notif_type="success").open()
            # Badge check
            from services.gamification_service import check_and_unlock_badges
            badges = check_and_unlock_badges(self.user_id, trigger="schedule_add")
            if badges:
                Clock.schedule_once(
                    lambda *_: Snackbar(text=f"🏅 {badges[0]}", notif_type="success").open(), 1)
        else:
            Snackbar(text=err, notif_type="error").open()

    def _delete(self, schedule_id: int):
        from services.schedule_service import delete_schedule
        delete_schedule(schedule_id)
        self._refresh()
        Snackbar(text="Class removed.", notif_type="info").open()
