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

Builder.load_string("""
<OnboardingScreen>:
    name: 'onboarding'
    MDBoxLayout:
        orientation: 'vertical'
        padding: dp(32)
        spacing: dp(20)

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

        MDTextField:
            id: name_field
            hint_text: 'Your name'
            icon_left: 'account'
            size_hint_y: None
            height: dp(56)
            mode: 'rectangle'

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

        MDRaisedButton:
            id: start_btn
            text: 'GET STARTED'
            size_hint_y: None
            height: dp(50)
            md_bg_color: app.theme_cls.primary_color
            on_release: root.on_start()
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
            Snackbar(text="Please enter your name.").open()
            return
        gender = "girl" if "girl" in self._selected_avatar else "boy"
        from services.auth_service import create_profile
        ok, err, user = create_profile(name, self._selected_avatar, gender)
        if ok:
            # Run first-time gamification seed
            from database.repositories import StreakRepository
            StreakRepository().record_today(user.id)
            from kivymd.app import MDApp
            MDApp.get_running_app().on_new_user(user.id)
        else:
            Snackbar(text=err or "Error saving profile.").open()
