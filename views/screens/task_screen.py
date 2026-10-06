"""
Tasklyn — Task Manager Screen
================================
Full CRUD with filters, search, sort, colour labels, and recurring tasks.
"""
from __future__ import annotations
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.button import MDRaisedButton, MDIconButton, MDFlatButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.menu import MDDropdownMenu
from utils.helpers import TasklynSnackbar as Snackbar
from kivymd.uix.selectioncontrol import MDSwitch
from kivymd.uix.pickers import MDDatePicker, MDTimePicker
from views.widgets import TaskCard

Builder.load_string("""
<TaskScreen>:
    name: 'tasks'
    MDBoxLayout:
        orientation: 'vertical'

        MDTopAppBar:
            title: 'Tasks'
            elevation: 0
            right_action_items: [['filter-variant', lambda x: root.show_filter_menu(x)]]

        MDCard:
            size_hint_y: None
            height: dp(56)
            padding: dp(8)
            radius: [dp(28)]
            elevation: 1
            md_bg_color: [1, 1, 1, 0.05] if app.theme_cls.theme_style == 'Dark' else [0, 0, 0, 0.02]
            pos_hint: {'center_x': .5}
            size_hint_x: 0.92
            
            MDTextField:
                id: search_field
                hint_text: 'Search tasks…'
                icon_left: 'magnify'
                mode: 'fill'
                radius: [dp(20)]
                on_text: root.on_search(self.text)
                
        Widget:
            size_hint_y: None
            height: dp(8)

        MDFloatLayout:
            MDScrollView:
                MDBoxLayout:
                    id: task_list
                    orientation: 'vertical'
                    padding: dp(16)
                    spacing: dp(12)
                    size_hint_y: None
                    height: self.minimum_height
            
            MDFloatingActionButton:
                icon: "plus"
                md_bg_color: app.theme_cls.primary_color
                pos_hint: {"right": 0.95, "y": 0.05}
                on_release: root.open_create_dialog()
""")


class _TaskFormContent(MDBoxLayout):
    def __init__(self, subjects, task=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(16)
        self.padding = [dp(4), dp(10), dp(4), dp(10)]
        self.size_hint_y = None
        
        self.task = task

        self.title_f = MDTextField(hint_text="Task title *", text=task.title if task else "", mode="fill", radius=[dp(10)])
        self.desc_f  = MDTextField(hint_text="Description", multiline=True,
                                    text=task.description if task else "", mode="fill", radius=[dp(10)])
        # Date & Time picker text fields
        self.dead_f = MDTextField(
            hint_text="Deadline (YYYY-MM-DD)",
            text=task.deadline[:10] if task and task.deadline else "",
            mode="fill", radius=[dp(10)]
        )
        self.dead_f.bind(focus=self.show_date_picker)

        self.remind_f = MDTextField(
            hint_text="Reminder (YYYY-MM-DD HH:MM)",
            text=task.reminder_at if task and task.reminder_at else "",
            mode="fill", radius=[dp(10)]
        )
        self.remind_f.bind(focus=self.show_time_picker)

        for w in [self.title_f, self.desc_f, self.dead_f, self.remind_f]:
            self.add_widget(w)



        # Priority row
        prow = MDBoxLayout(orientation="horizontal", spacing=dp(4),
                           size_hint_y=None, height=dp(40))
        prow.add_widget(MDLabel(text="Priority:", size_hint_x=None, width=dp(60)))
        self._priority = "medium"
        for p in ["low", "medium", "high"]:
            btn = MDFlatButton(text=p.capitalize(), size_hint_x=1, height=dp(34),
                               md_bg_color=[1,1,1,0.05],
                               on_release=lambda *_, pp=p: setattr(self, "_priority", pp))
            prow.add_widget(btn)
        self.add_widget(prow)

        # Recurring switch
        rrow = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(40))
        rrow.add_widget(MDLabel(text="Recurring task:"))
        self._recurring = MDSwitch()
        self._recurring.active = task.is_recurring if task else False
        rrow.add_widget(self._recurring)
        self.add_widget(rrow)

    def _force_portrait(self):
        from kivymd.app import MDApp
        MDApp.get_running_app().theme_cls.device_orientation = "portrait"

    def show_date_picker(self, instance_textfield, focus):
        if not focus:
            return
        instance_textfield.focus = False
        self._force_portrait()
        date_dialog = MDDatePicker()

        def on_save(instance, value, date_range):
            instance_textfield.text = value.strftime("%Y-%m-%d")

        date_dialog.bind(on_save=on_save)
        date_dialog.open()

    def show_time_picker(self, instance_textfield, focus):
        if not focus:
            return
        instance_textfield.focus = False
        self._force_portrait()
        date_dialog = MDDatePicker()

        def on_date_save(instance, value, date_range):
            self._force_portrait()
            time_dialog = MDTimePicker()

            def on_time_save(t_instance, t_value):
                instance_textfield.text = (
                    f"{value.strftime('%Y-%m-%d')} {t_value.strftime('%H:%M')}"
                )

            time_dialog.bind(on_save=on_time_save)
            time_dialog.open()

        date_dialog.bind(on_save=on_date_save)
        date_dialog.open()

class TaskScreen(MDScreen):
    def __init__(self, user_id: int, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self._filter_status: str | None = "pending"
        self._search_text = ""
        self._dialog: MDDialog | None = None
        Clock.schedule_once(self._refresh)

    def on_enter(self):
        self._refresh()

    def _refresh(self, *_):
        from services.task_service import get_user_tasks, get_subjects
        tasks = get_user_tasks(
            self.user_id, status=self._filter_status,
            search=self._search_text,
        )
        self._subjects = {s.id: s for s in get_subjects(self.user_id)}
        box = self.ids.task_list
        box.clear_widgets()
        if not tasks:
            box.add_widget(MDLabel(text="No tasks found.", halign="center",
                                   theme_text_color="Hint", font_style="Body1",
                                   size_hint_y=None, height=dp(60)))
        for t in tasks:
            subj = self._subjects.get(t.subject_id)
            card = TaskCard(
                task_id=t.id, title=t.title, priority=t.priority,
                deadline=t.deadline[:10] if t.deadline else "",
                label_color=t.label_color, is_done=(t.status == "done"),
                subject_name=subj.name if subj else "",
                completed_at=t.completed_at[:16] if t.completed_at else "",
            )
            card.on_complete_callback = self._complete_task
            card.on_tap_callback = self._open_edit_dialog
            box.add_widget(card)

    def on_search(self, text: str):
        self._search_text = text
        Clock.schedule_once(self._refresh, 0.3)

    def show_filter_menu(self, button):
        items = [
            {"text": "To Do",        "viewclass": "OneLineListItem",
             "on_release": lambda: self._set_filter("pending")},
            {"text": "Completed",       "viewclass": "OneLineListItem",
             "on_release": lambda: self._set_filter("done")},
        ]
        MDDropdownMenu(caller=button, items=items, width_mult=3).open()

    def _set_filter(self, status):
        self._filter_status = status
        self._refresh()

    def open_create_dialog(self, *_):
        from services.task_service import get_subjects
        subjects = get_subjects(self.user_id)
        
        content = _TaskFormContent(subjects)
        content.bind(minimum_height=content.setter('height'))
        
        from kivy.core.window import Window
        from kivymd.uix.scrollview import MDScrollView
        scroll = MDScrollView(size_hint_y=None)
        scroll.height = min(dp(450), Window.height - dp(200))
        scroll.add_widget(content)
        
        self._dialog = MDDialog(
            title="New Task",
            type="custom",
            content_cls=scroll,
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda *_: self._dialog.dismiss()),
                MDRaisedButton(text="SAVE",  on_release=lambda *_: self._save_task(content)),
            ],
        )
        self._dialog.open()

    def _open_edit_dialog(self, task_id: int):
        from services.task_service import get_task, get_subjects
        task = get_task(task_id)
        if not task:
            return
        subjects = get_subjects(self.user_id)
        
        content = _TaskFormContent(subjects, task=task)
        content.bind(minimum_height=content.setter('height'))
        
        from kivy.core.window import Window
        from kivymd.uix.scrollview import MDScrollView
        scroll = MDScrollView(size_hint_y=None)
        scroll.height = min(dp(450), Window.height - dp(200))
        scroll.add_widget(content)
        
        self._dialog = MDDialog(
            title="Edit Task",
            type="custom",
            content_cls=scroll,
            buttons=[
                MDFlatButton(text="DELETE", text_color=[1,0.3,0.3,1], on_release=lambda *_: self._delete_task(task_id)),
                MDFlatButton(text="CANCEL", on_release=lambda *_: self._dialog.dismiss()),
                MDRaisedButton(text="UPDATE", on_release=lambda *_: self._update_task(task_id, content)),
            ],
        )
        self._dialog.open()

    def _save_task(self, content: _TaskFormContent):
        from services.task_service import create_task
        ok, err, task = create_task(
            self.user_id,
            title=content.title_f.text,
            description=content.desc_f.text,
            priority=content._priority,
            deadline=content.dead_f.text or None,
            reminder_at=content.remind_f.text or None,
            is_recurring=content._recurring.active,
        )
        if ok:
            self._dialog.dismiss()
            self._refresh()
            Snackbar(text="Task created!").open()
        else:
            Snackbar(text=err).open()

    def _update_task(self, task_id: int, content: _TaskFormContent):
        from services.task_service import update_task
        ok, err = update_task(
            task_id,
            title=content.title_f.text,
            description=content.desc_f.text,
            priority=content._priority,
            deadline=content.dead_f.text or None,
            reminder_at=content.remind_f.text or None,
            is_recurring=content._recurring.active,
        )
        if ok:
            self._dialog.dismiss()
            self._refresh()
            Snackbar(text="Task updated!").open()
        else:
            Snackbar(text=err).open()

    def _complete_task(self, task_id: int):
        from services.task_service import complete_task
        ok, badges = complete_task(task_id, self.user_id)
        if ok:
            self._refresh()
            Snackbar(text="✅ Task done!").open()
            if badges:
                Clock.schedule_once(
                    lambda *_: Snackbar(text=f"🏅 {badges[0]}").open(), 1)

    def _delete_task(self, task_id: int):
        from services.task_service import delete_task
        delete_task(task_id)
        if self._dialog:
            self._dialog.dismiss()
        self._refresh()
        Snackbar(text="Task deleted.").open()
