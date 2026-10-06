"""
Tasklyn — Login Screen
=========================
Log in to an existing profile.
"""
from __future__ import annotations
from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from utils.helpers import TasklynSnackbar as Snackbar
from kivymd.app import MDApp
from kivy.clock import Clock

Builder.load_string("""
<LoginScreen>:
    name: 'login'
    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(32)
        spacing: dp(20)

        Image:
            source: 'tasklyn_logo_clear.png'
            size_hint: None, None
            size: dp(120), dp(120)
            pos_hint: {'center_x': .5}

        MDLabel:
            text: 'Welcome Back to Tasklyn'
            font_style: 'H4'
            bold: True
            halign: 'center'
            size_hint_y: None
            height: dp(50)

        MDLabel:
            text: "Please log in to continue"
            font_style: 'Subtitle1'
            halign: 'center'
            theme_text_color: 'Secondary'
            size_hint_y: None
            height: dp(30)
            
        MDCard:
            orientation: 'vertical'
            padding: dp(24)
            spacing: dp(20)
            size_hint_y: None
            height: self.minimum_height
            pos_hint: {'center_x': .5}
            radius: [dp(16)]
            elevation: 2
            md_bg_color: [1, 1, 1, 0.05] if app.theme_cls.theme_style == 'Dark' else [0, 0, 0, 0.02]

            MDTextField:
                id: name_field
                hint_text: 'Your name'
                icon_left: 'account'
                size_hint_y: None
                height: dp(56)
                mode: 'fill'
                radius: [dp(10)]

            MDRelativeLayout:
                size_hint_y: None
                height: dp(56)

                MDTextField:
                    id: password_field
                    hint_text: 'Password'
                    icon_left: 'lock'
                    password: True
                    mode: 'fill'
                    radius: [dp(10)]

                MDIconButton:
                    icon: 'eye-off'
                    pos_hint: {'center_y': .5}
                    pos: password_field.width - self.width + dp(8), 0
                    on_release:
                        self.icon = 'eye' if self.icon == 'eye-off' else 'eye-off'
                        password_field.password = not password_field.password
                
            Widget:
                size_hint_y: None
                height: dp(10)

            MDRaisedButton:
                id: login_btn
                text: 'LOG IN'
                font_style: 'Button'
                bold: True
                size_hint_x: 1
                size_hint_y: None
                height: dp(50)
                md_bg_color: app.theme_cls.primary_color
                on_release: root.on_login()

            MDFlatButton:
                text: "Don't have an account? Sign Up"
                pos_hint: {'center_x': .5}
                size_hint_x: 1
                on_release: root.go_to_signup() 
               
        Widget:
            size_hint_y: 1
""")


class LoginScreen(MDScreen):
    def on_login(self):
        name = self.ids.name_field.text.strip()
        password = self.ids.password_field.text.strip() or None
        if not name:
            Snackbar(text="Please enter your name.", notif_type="error").open()
            return
            
        from services.auth_service import authenticate
        ok, err, user = authenticate(name, password)
        if ok and user:
            # Login successful
            app = MDApp.get_running_app()
            app._user_id = user.id
            from views.screens.main_screen import MainScreen
            sm = app.root
            if "main" not in [s.name for s in sm.screens]:
                main = MainScreen(user_id=user.id)
                sm.add_widget(main)
            sm.current = "main"
            Clock.schedule_interval(lambda _: app._dispatch_notifications(), 60)
            Clock.schedule_once(lambda _: app._auto_backup(), 2)
        else:
            Snackbar(text=err or "Invalid credentials.", notif_type="error").open()

    def go_to_signup(self):
        app = MDApp.get_running_app()
        app.root.current = "onboarding"