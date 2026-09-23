"""
Tasklyn — Badges Screen
=========================
Displays all badges (locked and unlocked) organised by category.
"""
from __future__ import annotations
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton

Builder.load_string("""
<BadgesScreen>:
    name: 'badges'
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: 'Badges'
            elevation: 0
            left_action_items: [["arrow-left", lambda x: setattr(root.manager, 'current', 'main')]]
        MDScrollView:
            MDBoxLayout:
                id: content
                orientation: 'vertical'
                padding: dp(12)
                spacing: dp(16)
                size_hint_y: None
                height: self.minimum_height
""")


class BadgesScreen(MDScreen):
    def __init__(self, user_id: int, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        Clock.schedule_once(self._build)

    def on_enter(self):
        self._build()

    def _build(self, *_):
        from services.gamification_service import get_badges
        badges = get_badges(self.user_id)
        box = self.ids.content
        box.clear_widgets()

        # Summary
        unlocked = sum(1 for b in badges if b.is_unlocked)
        box.add_widget(MDLabel(
            text=f"[b]{unlocked}[/b] / {len(badges)} badges unlocked",
            markup=True, halign="center", font_style="Subtitle1",
            size_hint_y=None, height=dp(36),
        ))

        # Group by category
        categories: dict[str, list] = {}
        for b in badges:
            categories.setdefault(b.category, []).append(b)

        for cat, badge_list in categories.items():
            box.add_widget(MDLabel(
                text=f"[b]{cat.replace('_',' ').title()}[/b]",
                markup=True, font_style="Subtitle2",
                size_hint_y=None, height=dp(28),
            ))
            grid = MDGridLayout(cols=3, spacing=dp(10), padding=[0, 0, 0, dp(4)],
                                size_hint_y=None)
            grid.bind(minimum_height=grid.setter("height"))
            for badge in badge_list:
                grid.add_widget(self._badge_tile(badge))
            box.add_widget(grid)

    def _badge_tile(self, badge) -> MDCard:
        locked = not badge.is_unlocked
        card = MDCard(orientation="vertical",
                      padding=[dp(8), dp(10)],
                      spacing=dp(4),
                      size_hint_y=None, height=dp(110),
                      radius=[dp(14)],
                      elevation=3 if not locked else 1)
        if locked:
            card.md_bg_color = [0.15, 0.15, 0.22, 1]

        icon_btn = MDIconButton(
            icon=badge.icon if not locked else "lock",
            icon_size="28sp",
            theme_icon_color="Custom",
            icon_color=([1, 0.7, 0, 1] if not locked else [0.35, 0.35, 0.45, 1]),
            pos_hint={"center_x": .5},
        )
        card.add_widget(icon_btn)
        card.add_widget(MDLabel(
            text=badge.name, font_style="Caption",
            halign="center", theme_text_color="Primary" if not locked else "Secondary",
        ))
        if not locked and badge.unlocked_at:
            card.add_widget(MDLabel(
                text=badge.unlocked_at[:10],
                font_style="Caption", halign="center",
                theme_text_color="Hint",
            ))
        return card
