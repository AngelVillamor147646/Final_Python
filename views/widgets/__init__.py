"""
Tasklyn — Reusable Widget Library
=====================================
All shared UI widgets used across multiple screens.
"""
from __future__ import annotations
import io
from kivy.clock import Clock
from kivy.graphics import Color, Ellipse, RoundedRectangle, Line
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.properties import (
    BooleanProperty, ColorProperty, NumericProperty, StringProperty,
)
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.widget import Widget
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.button import MDFlatButton, MDRaisedButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDLabel
from kivymd.uix.progressbar import MDProgressBar

from themes import theme_manager as tm


Builder.load_string("""
<StatCard>:
    orientation: 'vertical'
    padding: dp(16)
    spacing: dp(4)
    size_hint_y: None
    height: dp(90)
    radius: [dp(16)]
    md_bg_color: app.theme_cls.bg_dark if app.theme_cls.theme_style == 'Dark' else app.theme_cls.bg_light

<GradientCard>:
    size_hint_y: None
    height: dp(80)
    padding: dp(14)
    radius: [dp(14)]

<PomodoroRingWidget>:
    size_hint: None, None
    size: dp(200), dp(200)
""")


# ─────────────────────────────────────────────────────────────────────────────
# StatCard — small KPI card for the dashboard
# ─────────────────────────────────────────────────────────────────────────────

class StatCard(MDCard):
    """A metric card with a title, value, and optional icon."""
    icon = StringProperty("chart-bar")
    title = StringProperty("Stat")
    value = StringProperty("0")
    accent_color = ColorProperty([0.49, 0.30, 1, 1])

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = [dp(4), dp(10)]
        self.spacing = dp(2)
        self.size_hint_y = None
        self.height = dp(90)
        self.elevation = 2
        self.radius = [dp(14)]
        Clock.schedule_once(self._build)

    def _build(self, *_):
        from kivymd.uix.label import MDLabel, MDIcon
        
        # Icon at top
        icon_lbl = MDIcon(icon=self.icon, font_size="22sp",
                          theme_text_color="Custom",
                          text_color=self.accent_color,
                          halign="center", size_hint_y=None, height=dp(26))
        self.add_widget(icon_lbl)
        
        # Value in middle
        self._value_lbl = MDLabel(text=self.value, font_style="H6",
                                   bold=True, theme_text_color="Primary",
                                   halign="center", size_hint_y=None, height=dp(28))
        self.add_widget(self._value_lbl)
        
        # Title at bottom
        title_lbl = MDLabel(text=self.title, font_style="Caption",
                            theme_text_color="Secondary",
                            halign="center", size_hint_y=None, height=dp(16))
        self.add_widget(title_lbl)
        
        self.bind(value=lambda _, v: setattr(self._value_lbl, "text", v))


# ─────────────────────────────────────────────────────────────────────────────
# ProgressRing — circular progress widget drawn on canvas
# ─────────────────────────────────────────────────────────────────────────────

class ProgressRing(Widget):
    """
    Circular progress ring drawn with Kivy canvas instructions.
    ``progress`` is 0.0–1.0.
    """
    progress = NumericProperty(0.0)
    ring_width = NumericProperty(dp(10))
    track_color = ColorProperty([0.18, 0.18, 0.29, 1])
    fill_color = ColorProperty([0.49, 0.30, 1.0, 1])
    label_text = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.bind(pos=self._redraw, size=self._redraw, progress=self._redraw)
        Clock.schedule_once(self._redraw)

    def _redraw(self, *_):
        import math
        self.canvas.clear()
        cx, cy = self.center
        r = min(self.width, self.height) / 2 - self.ring_width
        with self.canvas:
            # Track
            Color(*self.track_color)
            Line(circle=(cx, cy, r), width=self.ring_width, cap="round")
            # Fill arc
            Color(*self.fill_color)
            angle = self.progress * 360
            Line(circle=(cx, cy, r, 90, 90 - angle), width=self.ring_width, cap="round")


# ─────────────────────────────────────────────────────────────────────────────
# TaskCard widget
# ─────────────────────────────────────────────────────────────────────────────

class TaskCard(MDCard):
    task_id = NumericProperty(0)
    title = StringProperty("")
    priority = StringProperty("medium")
    deadline = StringProperty("")
    label_color = StringProperty("#7C4DFF")
    is_done = BooleanProperty(False)
    subject_name = StringProperty("")
    completed_at = StringProperty("")

    on_complete_callback = None   # callable(task_id)
    on_tap_callback = None        # callable(task_id)

    PRIORITY_ICONS = {"low": "arrow-down", "medium": "minus",
                      "high": "arrow-up", "critical": "alert"}

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.padding = [dp(12), dp(10)]
        self.spacing = dp(10)
        self.size_hint_y = None
        self.height = dp(72)
        self.elevation = 2
        self.radius = [dp(12)]
        Clock.schedule_once(self._build)

    def _build(self, *_):
        from kivymd.uix.selectioncontrol import MDCheckbox
        from kivy.uix.boxlayout import BoxLayout

        # Left colour strip
        strip_color = "#4CAF50" if self.is_done else self.label_color
        with self.canvas.before:
            from utils.helpers import hex_to_kivy_colour
            Color(*hex_to_kivy_colour(strip_color))
            self._strip = RoundedRectangle(
                pos=(self.x, self.y), size=(dp(4), self.height),
                radius=[dp(4)],
            )
        self.bind(pos=self._update_strip, size=self._update_strip)

        # Checkbox
        cb = MDCheckbox(size_hint=(None, None), size=(dp(36), dp(36)),
                        active=self.is_done)
        cb.bind(active=self._on_checkbox)
        self.add_widget(cb)

        # Text column
        col = BoxLayout(orientation="vertical", spacing=dp(2))
        self._title_lbl = MDLabel(text=self.title, font_style="Body1",
                                   theme_text_color="Primary",
                                   shorten=True, shorten_from="right",
                                   max_lines=1)
        col.add_widget(self._title_lbl)

        row2 = BoxLayout(orientation="horizontal", spacing=dp(8),
                         size_hint_y=None, height=dp(18))
        self._subj_lbl = MDLabel(text=self.subject_name, font_style="Caption",
                                  theme_text_color="Secondary")
        
        status_text = f"Completed at {self.completed_at}" if self.is_done and self.completed_at else self.deadline
        self._dead_lbl = MDLabel(text=status_text, font_style="Caption",
                                  theme_text_color="Hint" if not self.is_done else "Custom", text_color=[0.3, 0.7, 0.3, 1] if self.is_done else [0.5, 0.5, 0.5, 1])
        row2.add_widget(self._subj_lbl)
        row2.add_widget(self._dead_lbl)
        col.add_widget(row2)
        self.add_widget(col)

        # Priority icon
        picon = MDIconButton(
            icon=self.PRIORITY_ICONS.get(self.priority, "minus"),
            icon_size="16sp",
            size_hint=(None, None), size=(dp(30), dp(30)),
        )
        self.add_widget(picon)
        self.bind(on_release=lambda *_: self._on_tap())

    def _update_strip(self, *_):
        if hasattr(self, "_strip"):
            self._strip.pos = (self.x + dp(1), self.y + dp(6))
            self._strip.size = (dp(4), self.height - dp(12))

    def _on_checkbox(self, cb, value):
        if value and self.on_complete_callback:
            self.on_complete_callback(self.task_id)

    def _on_tap(self):
        if self.on_tap_callback:
            self.on_tap_callback(self.task_id)


# ─────────────────────────────────────────────────────────────────────────────
# BadgeChip
# ─────────────────────────────────────────────────────────────────────────────

class BadgeChip(MDCard):
    """Small badge display chip showing icon + name."""
    badge_icon = StringProperty("trophy")
    badge_name = StringProperty("")
    is_unlocked = BooleanProperty(False)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.padding = [dp(10), dp(6)]
        self.spacing = dp(8)
        self.size_hint_y = None
        self.height = dp(44)
        self.radius = [dp(22)]
        self.elevation = 1
        Clock.schedule_once(self._build)

    def _build(self, *_):
        icon = MDIconButton(icon=self.badge_icon, icon_size="18sp",
                            size_hint=(None, None), size=(dp(28), dp(28)),
                            theme_icon_color="Custom",
                            icon_color=([1, 0.7, 0, 1] if self.is_unlocked
                                        else [0.4, 0.4, 0.5, 1]))
        self.add_widget(icon)
        lbl = MDLabel(text=self.badge_name, font_style="Caption",
                      theme_text_color="Primary" if self.is_unlocked else "Secondary")
        self.add_widget(lbl)


# ─────────────────────────────────────────────────────────────────────────────
# ChartImage — wraps PNG bytes into a Kivy Image widget
# ─────────────────────────────────────────────────────────────────────────────

class ChartImage(BoxLayout):
    """Displays a PNG chart (bytes) inside a rounded card."""

    def __init__(self, png_bytes: bytes | None = None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self._img = None
        if png_bytes:
            self.update(png_bytes)

    def update(self, png_bytes: bytes) -> None:
        from kivy.uix.image import CoreImage
        from kivy.uix.image import Image as KvImage
        self.clear_widgets()
        buf = io.BytesIO(png_bytes)
        core_img = CoreImage(buf, ext="png")
        img = KvImage(texture=core_img.texture,
                      size_hint=(1, 1), allow_stretch=True, keep_ratio=True)
        self.add_widget(img)
        self._img = img
