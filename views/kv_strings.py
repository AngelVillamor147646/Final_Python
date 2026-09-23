"""
Tasklyn — KV string for the root app shell.
Loaded at startup by main.py.
"""

APP_KV = """
#:import get_color_from_hex kivy.utils.get_color_from_hex
#:import MDBottomNavigationItem kivymd.uix.bottomnavigation
#:import FadeTransition kivy.uix.screenmanager

<RootLayout>:
    orientation: 'vertical'

<TaskCard>:
    size_hint_y: None
    height: dp(72)
    padding: dp(12), dp(8)
    spacing: dp(10)
    canvas.before:
        Color:
            rgba: root.card_color
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]

<ProgressRing>:
    canvas.before:
        Color:
            rgba: root.track_color
        Ellipse:
            pos: self.pos
            size: self.size
        Color:
            rgba: root.progress_color
"""
