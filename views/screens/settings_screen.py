"""
Tasklyn — Settings Screen
===========================
Theme switching, notifications, profile editing, backup/restore/export.
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
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDSwitch
from utils.helpers import TasklynSnackbar as Snackbar

Builder.load_string("""
<SettingsScreen>:
    name: 'settings'
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: 'Settings'
            elevation: 0
            left_action_items: [["arrow-left", lambda x: setattr(root.manager, 'current', 'main')]]
        MDScrollView:
            MDBoxLayout:
                id: content
                orientation: 'vertical'
                padding: dp(16)
                spacing: dp(12)
                size_hint_y: None
                height: self.minimum_height
""")


def _section(title: str) -> MDLabel:
    return MDLabel(text=f"[b]{title}[/b]", markup=True, font_style="Subtitle2",
                   size_hint_y=None, height=dp(32))


def _row(label: str, widget) -> MDBoxLayout:
    row = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(48))
    row.add_widget(MDLabel(text=label, font_style="Body1"))
    row.add_widget(widget)
    return row


class SettingsScreen(MDScreen):
    def __init__(self, user_id: int, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        Clock.schedule_once(self._build)

    def _build(self, *_):
        from database.repositories import SettingsRepository
        settings = SettingsRepository()
        box = self.ids.content
        box.clear_widgets()

        # ── Profile ──
        box.add_widget(_section("Profile"))
        btn = MDRaisedButton(text="Edit Profile", size_hint_x=None, width=dp(160),
                              on_release=self._edit_profile)
        box.add_widget(btn)

        # ── Appearance ──
        box.add_widget(_section("Appearance"))
        self._theme_sw = MDSwitch(
            size_hint=(None, None), size=(dp(60), dp(32)),
        )
        self._theme_sw.active = (settings.get(self.user_id, "theme") == "Dark")
        self._theme_sw.bind(active=self._on_theme_toggle)
        box.add_widget(_row("Dark Mode", self._theme_sw))

        # ── Notifications ──
        box.add_widget(_section("Notifications"))
        self._notif_sw = MDSwitch(
            size_hint=(None, None), size=(dp(60), dp(32)),
        )
        self._notif_sw.active = settings.get_bool(self.user_id, "notifications_enabled")
        self._notif_sw.bind(active=lambda sw, v: settings.set(
            self.user_id, "notifications_enabled", "1" if v else "0"))
        box.add_widget(_row("Enable Notifications", self._notif_sw))

        # ── Backup & Data ──
        box.add_widget(_section("Backup & Data"))
        for label, handler in [
            ("Create Backup",     self._do_backup),
            ("Restore Backup",    self._do_restore),
            ("Export Tasks CSV",  self._export_csv),
            ("Export PDF Report", self._export_pdf),
        ]:
            btn = MDRaisedButton(text=label, size_hint_x=1, height=dp(44),
                                  on_release=handler)
            box.add_widget(btn)

        # ── Danger Zone ──
        box.add_widget(_section("Danger Zone"))
        rst_btn = MDRaisedButton(
            text="Reset All Settings",
            md_bg_color=[0.8, 0.2, 0.2, 1],
            size_hint_x=1, height=dp(44),
            on_release=self._confirm_reset,
        )
        box.add_widget(rst_btn)

    # ── Handlers ──────────────────────────────────────────────────────────

    def _on_theme_toggle(self, sw, is_dark: bool):
        from database.repositories import SettingsRepository
        from themes import theme_manager
        new_theme = "Dark" if is_dark else "Light"
        theme_manager.set_theme(new_theme, self._get_app())
        SettingsRepository().set(self.user_id, "theme", new_theme)
        Snackbar(text=f"Theme set to {new_theme}.").open()

    def _get_app(self):
        from kivymd.app import MDApp
        return MDApp.get_running_app()

    def _edit_profile(self, *_):
        from services.auth_service import get_active_user
        user = get_active_user()
        content = MDBoxLayout(orientation="vertical", spacing=dp(8),
                               size_hint_y=None, height=dp(120), padding=[dp(4)]*4)
        self._pname = MDTextField(hint_text="Your name", text=user.name if user else "")
        content.add_widget(self._pname)
        dlg = MDDialog(
            title="Edit Profile", type="custom", content_cls=content,
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda *_: dlg.dismiss()),
                MDRaisedButton(text="SAVE",
                               on_release=lambda *_, d=dlg: self._save_profile(d)),
            ],
        )
        dlg.open()

    def _save_profile(self, dlg):
        from services.auth_service import get_active_user, update_profile
        user = get_active_user()
        ok, err = update_profile(self._pname.text, user.avatar_id, user.gender)
        dlg.dismiss()
        Snackbar(text="Profile updated!" if ok else err).open()

    def _do_backup(self, *_):
        from services.backup_service import create_backup
        path = create_backup()
        Snackbar(text=f"Backup saved: {path.name}").open()

    def _do_restore(self, *_):
        from services.backup_service import list_backups, restore_backup
        backups = list_backups()
        if not backups:
            Snackbar(text="No backups found.").open()
            return
        latest = backups[0]
        dlg = MDDialog(
            title="Restore Backup",
            text=f"Restore from: {latest.name}?\nThis will replace all current data.",
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda *_: dlg.dismiss()),
                MDRaisedButton(text="RESTORE",
                               on_release=lambda *_, d=dlg: self._do_restore_confirm(latest, d)),
            ],
        )
        dlg.open()

    def _do_restore_confirm(self, backup_path, dlg):
        from services.backup_service import restore_backup
        ok, msg = restore_backup(backup_path)
        dlg.dismiss()
        Snackbar(text=msg).open()

    def _export_csv(self, *_):
        from services.backup_service import export_tasks_csv
        path = export_tasks_csv(self.user_id)
        Snackbar(text=f"Exported: {path.name}").open()

    def _export_pdf(self, *_):
        from services.backup_service import export_stats_pdf
        ok, msg, _ = export_stats_pdf(self.user_id)
        Snackbar(text=msg).open()

    def _confirm_reset(self, *_):
        dlg = MDDialog(
            title="Reset Settings",
            text="This will reset all settings to defaults. Continue?",
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda *_: dlg.dismiss()),
                MDRaisedButton(text="RESET", md_bg_color=[0.8,0.2,0.2,1],
                               on_release=lambda *_, d=dlg: self._do_reset(d)),
            ],
        )
        dlg.open()

    def _do_reset(self, dlg):
        from database.repositories import SettingsRepository
        SettingsRepository().reset_to_defaults(self.user_id)
        dlg.dismiss()
        Snackbar(text="Settings reset to defaults.").open()
        self._build()
