"""
Tasklyn — Splash Screen
=========================
Shown for ~2 s while the database initialises, then routes to
Onboarding (first launch) or Dashboard.
"""
from __future__ import annotations
from kivy.clock import Clock
from kivy.graphics import Color, RoundedRectangle
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.animation import Animation
from kivymd.uix.screen import MDScreen
from kivymd.uix.label import MDLabel
from kivymd.uix.boxlayout import MDBoxLayout

Builder.load_string("""
<SplashScreen>:
    name: 'splash'
    MDBoxLayout:
        id: container
        orientation: 'vertical'
        halign: 'center'
        padding: dp(40)
        spacing: dp(20)
        pos_hint: {'center_x': .5, 'center_y': .5}

        Image:
            id: logo_img
            source: 'tasklyn_logo_clear.png'
            size_hint: None, None
            size: dp(150), dp(150)
            pos_hint: {'center_x': .5}
            opacity: 0

        MDLabel:
            id: name_lbl
            text: 'Tasklyn'
            font_style: 'H3'
            bold: True
            halign: 'center'
            theme_text_color: 'Custom'
            text_color: 1, 1, 1, 1
            opacity: 0

        MDLabel:
            id: tag_lbl
            text: 'Your Academic Companion'
            font_style: 'Subtitle2'
            halign: 'center'
            theme_text_color: 'Custom'
            text_color: .8, .8, 1, .7
            opacity: 0
""")


class SplashScreen(MDScreen):
    def on_enter(self):
        self._draw_bg()
        Clock.schedule_once(self._animate_in, 0.1)
        Clock.schedule_once(self._navigate, 2.4)

    def _draw_bg(self):
        with self.canvas.before:
            Color(0.07, 0.07, 0.18, 1)
            self._bg = RoundedRectangle(pos=self.pos, size=self.size)
        self.bind(pos=lambda *_: setattr(self._bg, "pos", self.pos),
                  size=lambda *_: setattr(self._bg, "size", self.size))

    def _animate_in(self, *_):
        logo = self.ids.logo_img
        name = self.ids.name_lbl
        tag  = self.ids.tag_lbl
        (Animation(opacity=1, duration=0.5, t="out_cubic") +
         Animation(opacity=1, duration=0.01)).start(logo)
        Clock.schedule_once(lambda *_: Animation(opacity=1, duration=0.4).start(name), 0.3)
        Clock.schedule_once(lambda *_: Animation(opacity=1, duration=0.4).start(tag), 0.6)

    def _navigate(self, *_):
        from services.auth_service import is_first_launch
        target = "onboarding" if is_first_launch() else "login"
        self.manager.current = target
