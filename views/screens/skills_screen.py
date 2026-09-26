"""
Tasklyn — Habits Screen
=========================
Displays user-defined habits with streaks and reminders.
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
from kivymd.uix.button import MDIconButton, MDRaisedButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from utils.helpers import TasklynSnackbar as Snackbar
from datetime import date

Builder.load_string("""
<SkillsScreen>:
    name: 'habits'
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: 'Habits'
            elevation: 0
            right_action_items: [['plus', lambda x: root.open_add_dialog()]]
            # Left action item removed since it's now in bottom nav
            
        MDScrollView:
            MDBoxLayout:
                id: content
                orientation: 'vertical'
                padding: dp(12)
                spacing: dp(12)
                size_hint_y: None
                height: self.minimum_height
""")

class SkillsScreen(MDScreen):
    def __init__(self, user_id: int, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self._dialog = None
        Clock.schedule_once(self._build)

    def on_enter(self):
        self._build()

    def _build(self, *_):
        from services.habit_service import get_user_habits
        habits = get_user_habits(self.user_id)
        box = self.ids.content
        box.clear_widgets()
        
        if not habits:
            box.add_widget(MDLabel(
                text="No habits yet. Click + to add one!",
                halign="center", theme_text_color="Hint",
                size_hint_y=None, height=dp(60)
            ))
            return

        for habit in habits:
            box.add_widget(self._habit_card(habit))

    def _habit_card(self, habit) -> MDCard:
        card = MDCard(orientation="horizontal", padding=[dp(16), dp(10)],
                      spacing=dp(12), size_hint_y=None, height=dp(80),
                      elevation=2, radius=[dp(12)])
        
        # Color strip based on completion
        today = date.today().isoformat()
        is_done = habit.last_completed and habit.last_completed.startswith(today)
        
        from kivy.graphics import Color, RoundedRectangle
        from utils.helpers import hex_to_kivy_colour
        strip_color = "#4CAF50" if is_done else "#FF9800"
        with card.canvas.before:
            Color(*hex_to_kivy_colour(strip_color))
            RoundedRectangle(pos=(card.x, card.y), size=(dp(4), dp(80)), radius=[dp(4)])
            
        # Text details
        col = MDBoxLayout(orientation="vertical", spacing=dp(2))
        title_text = f"[b]{habit.skill_name}[/b]"
        if habit.streak > 3:
            title_text += " 🔥"
            
        col.add_widget(MDLabel(text=title_text, markup=True, font_style="Subtitle1"))
        
        meta = f"Streak: {habit.streak} days  |  Longest: {habit.longest_streak}"
        if habit.reminder_time:
            meta += f"  |  Reminder: {habit.reminder_time}"
        col.add_widget(MDLabel(text=meta, font_style="Caption", theme_text_color="Secondary"))
        card.add_widget(col)
        
        # Actions
        if not is_done:
            btn_done = MDIconButton(icon="check-circle-outline", icon_size="24sp",
                                    theme_text_color="Custom", text_color=[0.3, 0.7, 0.3, 1],
                                    on_release=lambda *_, hid=habit.id: self._complete(hid))
            card.add_widget(btn_done)
            
        btn_del = MDIconButton(icon="delete-outline", icon_size="20sp",
                               theme_text_color="Hint",
                               on_release=lambda *_, hid=habit.id: self._delete(hid))
        card.add_widget(btn_del)

        return card

    def _complete(self, habit_id: int):
        from services.habit_service import complete_habit
        ok, msg = complete_habit(habit_id)
        if ok:
            Snackbar(text=msg, notif_type="success").open()
            self._build()
        else:
            Snackbar(text=msg, notif_type="error").open()
            
    def _delete(self, habit_id: int):
        from services.habit_service import delete_habit
        if delete_habit(habit_id):
            Snackbar(text="Habit deleted.", notif_type="info").open()
            self._build()

    def open_add_dialog(self):
        from kivymd.uix.dialog import MDDialog
        
        content = MDBoxLayout(orientation="vertical", spacing=dp(10),
                              size_hint_y=None, height=dp(150), padding=[dp(4)]*4)
        
        self._s_name = MDTextField(hint_text="Habit name (e.g. Reading)", text="")
        self._s_remind = MDTextField(hint_text="Reminder time (e.g. 08:00)", text="")
        content.add_widget(self._s_name)
        content.add_widget(self._s_remind)

        self._dialog = MDDialog(
            title="New Habit",
            type="custom", content_cls=content,
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda *_: self._dialog.dismiss()),
                MDRaisedButton(text="SAVE", on_release=self._save),
            ],
        )
        self._dialog.open()

    def _save(self, *_):
        from services.habit_service import create_habit
        
        ok, err, habit = create_habit(
            self.user_id, 
            name=self._s_name.text, 
            reminder_time=self._s_remind.text,
            notification_enabled=bool(self._s_remind.text)
        )
        if ok:
            self._dialog.dismiss()
            self._build()
            Snackbar(text="Habit added!", notif_type="success").open()
        else:
            Snackbar(text=err, notif_type="error").open()

