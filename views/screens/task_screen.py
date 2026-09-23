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
from views.widgets import TaskCard

Builder.load_string("""
<TaskScreen>:
    name: 'tasks'
    MDBoxLayout:
        orientation: 'vertical'

        MDTopAppBar:
            title: 'Tasks'
            elevation: 0
            right_action_items: [['filter-variant', lambda x: root.show_filter_menu(x)], ['plus-circle', lambda x: root.open_create_dialog()]]

        MDTextField:
            id: search_field
            hint_text: 'Search tasks…'
            icon_left: 'magnify'
            size_hint_y: None
            height: dp(48)
            on_text: root.on_search(self.text)

        MDScrollView:
            MDBoxLayout:
                id: task_list
                orientation: 'vertical'
                padding: dp(12)
                spacing: dp(8)
                size_hint_y: None
                height: self.minimum_height
""")


class _TaskFormContent(MDBoxLayout):
    def __init__(self, subjects, task=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = dp(10)
        self.padding = [dp(4), dp(4)]
        self.size_hint_y = None
        self.height = dp(400)
        self.task = task

        self.title_f = MDTextField(hint_text="Task title *", text=task.title if task else "")
        self.desc_f  = MDTextField(hint_text="Description", multiline=True,
                                    text=task.description if task else "")
        self.dead_f  = MDTextField(hint_text="Deadline (YYYY-MM-DD)",
                                    text=task.deadline[:10] if task and task.deadline else "")
        self.remind_f = MDTextField(hint_text="Reminder (YYYY-MM-DD HH:MM)",
                                     text=task.reminder_at if task else "")

        for w in [self.title_f, self.desc_f, self.dead_f, self.remind_f]:
            self.add_widget(w)

        # Priority row
        prow = MDBoxLayout(orientation="horizontal", spacing=dp(6),
                           size_hint_y=None, height=dp(40))
        prow.add_widget(MDLabel(text="Priority:", size_hint_x=None, width=dp(70)))
        self._priority = "medium"
        for p in ["low", "medium", "high", "critical"]:
            btn = MDRaisedButton(text=p.capitalize(), size_hint_x=1, height=dp(34),
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


class TaskScreen(MDScreen):
    def __init__(self, user_id: int, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self._filter_status: str | None = None
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
            )
            card.on_complete_callback = self._complete_task
            card.on_tap_callback = self._open_edit_dialog
            box.add_widget(card)

    def on_search(self, text: str):
        self._search_text = text
        Clock.schedule_once(self._refresh, 0.3)

    def show_filter_menu(self, button):
        items = [
            {"text": "All",        "viewclass": "OneLineListItem",
             "on_release": lambda: self._set_filter(None)},
            {"text": "Pending",    "viewclass": "OneLineListItem",
             "on_release": lambda: self._set_filter("pending")},
            {"text": "In Progress","viewclass": "OneLineListItem",
             "on_release": lambda: self._set_filter("in_progress")},
            {"text": "Done",       "viewclass": "OneLineListItem",
             "on_release": lambda: self._set_filter("done")},
            {"text": "Overdue",    "viewclass": "OneLineListItem",
             "on_release": lambda: self._set_filter("overdue")},
        ]
        MDDropdownMenu(caller=button, items=items, width_mult=3).open()

    def _set_filter(self, status):
        self._filter_status = status
        self._refresh()

    def open_create_dialog(self, *_):
        from services.task_service import get_subjects
        subjects = get_subjects(self.user_id)
        content = _TaskFormContent(subjects)
        self._dialog = MDDialog(
            title="New Task",
            type="custom",
            content_cls=content,
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
        self._dialog = MDDialog(
            title="Edit Task",
            type="custom",
            content_cls=content,
            buttons=[
                MDFlatButton(text="DELETE", on_release=lambda *_: self._delete_task(task_id)),
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
