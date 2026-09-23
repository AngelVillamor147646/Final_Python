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
            right_action_items: [['plus-circle', lambda x: root.open_add_dialog()]]

        MDBoxLayout:
            id: day_tabs
            orientation: 'horizontal'
            size_hint_y: None
            height: dp(44)
            padding: dp(4), 0
            spacing: dp(4)

        MDScrollView:
            MDBoxLayout:
                id: schedule_list
                orientation: 'vertical'
                padding: dp(12)
                spacing: dp(10)
                size_hint_y: None
                height: self.minimum_height
""")


class ScheduleScreen(MDScreen):
    def __init__(self, user_id: int, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self._selected_day = __import__("datetime").date.today().weekday()
        self._dialog = None
        Clock.schedule_once(self._build_day_tabs)

    def on_enter(self):
        self._refresh()

    def _build_day_tabs(self, *_):
        tabs = self.ids.day_tabs
        tabs.clear_widgets()
        for i, name in enumerate(DAY_NAMES):
            btn = MDRaisedButton(
                text=name, size_hint_x=1, height=dp(36),
                on_release=lambda *_, d=i: self._select_day(d),
            )
            if i == self._selected_day:
                btn.md_bg_color = [0.49, 0.30, 1, 1]
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
                      spacing=dp(12), size_hint_y=None, height=dp(72),
                      elevation=2, radius=[dp(12)])
        # Colour strip
        from kivy.graphics import Color, RoundedRectangle
        with card.canvas.before:
            Color(*hex_to_kivy_colour(sc.color))
            RoundedRectangle(pos=(card.x, card.y), size=(dp(4), dp(72)),
                             radius=[dp(4)])
        col = MDBoxLayout(orientation="vertical")
        col.add_widget(MDLabel(text=f"[b]{sc.title}[/b]", markup=True,
                               font_style="Body1"))
        meta = f"{sc.start_time} – {sc.end_time}"
        if sc.room: meta += f"  •  {sc.room}"
        col.add_widget(MDLabel(text=meta, font_style="Caption",
                               theme_text_color="Secondary"))
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
        content = MDBoxLayout(orientation="vertical", spacing=dp(8),
                              size_hint_y=None, height=dp(380), padding=[dp(4)]*4)
        self._s_title  = MDTextField(hint_text="Class title *", text="")
        self._s_start  = MDTextField(hint_text="Start time (HH:MM)", text="")
        self._s_end    = MDTextField(hint_text="End time (HH:MM)", text="")
        self._s_room   = MDTextField(hint_text="Room / location", text="")
        self._s_instr  = MDTextField(hint_text="Instructor", text="")
        self._s_remind = MDTextField(hint_text="Reminder (minutes before)", text="15")
        for w in [self._s_title, self._s_start, self._s_end,
                  self._s_room, self._s_instr, self._s_remind]:
            content.add_widget(w)

        self._dialog = MDDialog(
            title=f"Add Class — {DAY_NAMES[self._selected_day]}",
            type="custom", content_cls=content,
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda *_: self._dialog.dismiss()),
                MDRaisedButton(text="SAVE",  on_release=self._save),
            ],
        )
        self._dialog.open()

    def _save(self, *_):
        from services.schedule_service import create_schedule
        try:
            remind = int(self._s_remind.text or "15")
        except ValueError:
            remind = 15
        ok, err, sc = create_schedule(
            user_id=self.user_id,
            title=self._s_title.text,
            day_of_week=self._selected_day,
            start_time=self._s_start.text,
            end_time=self._s_end.text,
            room=self._s_room.text,
            instructor=self._s_instr.text,
            reminder_minutes=remind,
        )
        if ok:
            self._dialog.dismiss()
            self._refresh()
            Snackbar(text="Class added!").open()
            # Badge check
            from services.gamification_service import check_and_unlock_badges
            badges = check_and_unlock_badges(self.user_id, trigger="schedule_add")
            if badges:
                Clock.schedule_once(
                    lambda *_: Snackbar(text=f"🏅 {badges[0]}").open(), 1)
        else:
            Snackbar(text=err).open()

    def _delete(self, schedule_id: int):
        from services.schedule_service import delete_schedule
        delete_schedule(schedule_id)
        self._refresh()
        Snackbar(text="Class removed.").open()
