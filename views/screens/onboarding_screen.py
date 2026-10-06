"""
Tasklyn — Onboarding Screen
==============================
Step-by-step profile setup: name, gender, avatar selection.
"""
from __future__ import annotations
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDRaisedButton, MDFlatButton
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.card import MDCard
from utils.helpers import TasklynSnackbar as Snackbar
from config import AVATAR_SLUGS
import re

Builder.load_string("""
<OnboardingScreen>:
    name: 'onboarding'
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
            text: 'Welcome to Tasklyn'
            font_style: 'H4'
            bold: True
            halign: 'center'
            size_hint_y: None
            height: dp(50)

        MDLabel:
            text: "Let's set up your profile"
            font_style: 'Subtitle1'
            halign: 'center'
            theme_text_color: 'Secondary'
            size_hint_y: None
            height: dp(30)

        MDCard:
            orientation: 'vertical'
            padding: dp(20)
            spacing: dp(16)
            size_hint_y: None
            height: self.minimum_height
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
            
            MDLabel:
                text: '8+ characters, with a capital letter, number, and special character.'
                font_style: 'Caption'
                halign: 'left'
                theme_text_color: 'Secondary'
                size_hint_y: None
                height: dp(20)

            MDLabel:
                text: 'Choose your avatar'
                font_style: 'Subtitle2'
                size_hint_y: None
                height: dp(28)

            ScrollView:
                size_hint_y: None
                height: dp(110)
                MDGridLayout:
                    id: avatar_grid
                    cols: 4
                    spacing: dp(10)
                    padding: dp(4)
                    size_hint_y: None
                    height: self.minimum_height

            Widget:
                size_hint_y: None
                height: dp(10)

            MDRaisedButton:
                id: start_btn
                text: 'GET STARTED'
                font_style: 'Button'
                bold: True
                size_hint_x: 1
                size_hint_y: None
                height: dp(50)
                md_bg_color: app.theme_cls.primary_color
                on_release: root.on_start()
                
        Widget:
            size_hint_y: 1
""")


class _AvatarCard(MDCard):
    def __init__(self, slug: str, is_selected: bool, on_select, **kwargs):
        super().__init__(**kwargs)
        self.slug = slug
        self.radius = [dp(12)]
        self.size_hint = None, None
        self.size = dp(70), dp(70)
        self.elevation = 3 if is_selected else 1
        self.on_select = on_select
        self._build()

    def _build(self):
        icon_name = self._slug_to_icon()
        from kivymd.uix.button import MDIconButton
        btn = MDIconButton(icon=icon_name, icon_size="36sp",
                           pos_hint={"center_x": .5, "center_y": .5})
        btn.bind(on_release=lambda *_: self.on_select(self.slug))
        self.add_widget(btn)

    def _slug_to_icon(self) -> str:
        mapping = {
            "boy_neutral": "face-man",       "boy_smile":   "face-man-shimmer",
            "boy_sad":     "emoticon-sad",    "boy_star":    "star-face",
            "girl_neutral":"face-woman",      "girl_smile":  "face-woman-shimmer",
            "girl_sad":    "emoticon-sad",    "girl_star":   "star-face",
        }
        return mapping.get(self.slug, "account-circle")


class OnboardingScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._selected_avatar = AVATAR_SLUGS[0]
        self._avatar_cards: dict[str, _AvatarCard] = {}
        Clock.schedule_once(self._populate_avatars)

    def _populate_avatars(self, *_):
        grid = self.ids.avatar_grid
        grid.clear_widgets()
        for slug in AVATAR_SLUGS:
            card = _AvatarCard(
                slug=slug,
                is_selected=(slug == self._selected_avatar),
                on_select=self._select_avatar,
            )
            self._avatar_cards[slug] = card
            grid.add_widget(card)

    def _select_avatar(self, slug: str):
        self._selected_avatar = slug
        for s, card in self._avatar_cards.items():
            card.elevation = 6 if s == slug else 1
            card.md_bg_color = ([0.49, 0.30, 1, 0.25] if s == slug
                                 else [0, 0, 0, 0])

    def on_start(self):
        name = self.ids.name_field.text.strip()
        if not name:
            Snackbar(text="Please enter your name.", notif_type="error").open()
            return
        password = self.ids.password_field.text.strip() or None

        if password:
            if len(password) < 8:
                Snackbar(text="Password must be at least 8 characters.", notif_type="error").open()
                return
            if not re.search(r'[A-Z]', password):
                Snackbar(text="Password must include an uppercase letter.", notif_type="error").open()
                return
            if not re.search(r'[0-9]', password):
                Snackbar(text="Password must include a number.", notif_type="error").open()
                return
            if not re.search(r'[^A-Za-z0-9]', password):
                Snackbar(text="Password must include a special character.", notif_type="error").open()
                return

        gender = "girl" if "girl" in self._selected_avatar else "boy"
        from services.auth_service import create_profile
        ok, err, user = create_profile(name, self._selected_avatar, gender, password)
        if ok:
            # Run first-time gamification seed
            from database.repositories import StreakRepository
            StreakRepository().record_today(user.id)
            from kivymd.app import MDApp
            MDApp.get_running_app().on_new_user(user.id)
        else:
            Snackbar(text=err or "Error saving profile.", notif_type="error").open()
