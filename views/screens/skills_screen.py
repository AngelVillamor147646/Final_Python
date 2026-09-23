"""
Tasklyn — Skills Screen
=========================
Displays 5 skills with XP progress bars, level, and total XP.
"""
from __future__ import annotations
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.progressbar import MDProgressBar
from kivymd.uix.button import MDIconButton

Builder.load_string("""
<SkillsScreen>:
    name: 'skills'
    MDBoxLayout:
        orientation: 'vertical'
        MDTopAppBar:
            title: 'Skills'
            elevation: 0
            left_action_items: [["arrow-left", lambda x: setattr(root.manager, 'current', 'main')]]
        MDScrollView:
            MDBoxLayout:
                id: content
                orientation: 'vertical'
                padding: dp(12)
                spacing: dp(12)
                size_hint_y: None
                height: self.minimum_height
""")


class SkillsScreen(MDScreen):
    def __init__(self, user_id: int, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        Clock.schedule_once(self._build)

    def on_enter(self):
        self._build()

    def _build(self, *_):
        from services.gamification_service import get_skills
        skills = get_skills(self.user_id)
        box = self.ids.content
        box.clear_widgets()
        box.add_widget(MDLabel(
            text="[b]Your Skill Tree[/b]",
            markup=True, font_style="H6",
            size_hint_y=None, height=dp(40),
        ))
        for skill in skills:
            box.add_widget(self._skill_card(skill))

    def _skill_card(self, skill) -> MDCard:
        card = MDCard(orientation="vertical", padding=[dp(16), dp(14)],
                      spacing=dp(8), size_hint_y=None, height=dp(120),
                      elevation=3, radius=[dp(16)])
        # Header row
        header = MDBoxLayout(orientation="horizontal", size_hint_y=None, height=dp(32))
        icon = MDIconButton(icon=skill.icon, icon_size="20sp",
                            size_hint=(None, None), size=(dp(32), dp(32)),
                            theme_icon_color="Custom",
                            icon_color=[0.49, 0.30, 1, 1])
        header.add_widget(icon)
        header.add_widget(MDLabel(text=f"[b]{skill.name}[/b]",
                                   markup=True, font_style="Subtitle1"))
        lvl_lbl = MDLabel(text=f"Lv {skill.current_level}",
                           font_style="Subtitle2", halign="right",
                           theme_text_color="Primary")
        header.add_widget(lvl_lbl)
        card.add_widget(header)

        # Progress bar
        progress = skill.current_xp / max(skill.xp_per_level, 1)
        bar = MDProgressBar(value=progress * 100, size_hint_y=None, height=dp(8))
        card.add_widget(bar)

        # XP label
        card.add_widget(MDLabel(
            text=f"{skill.current_xp} / {skill.xp_per_level} XP  •  Total: {skill.total_xp} XP",
            font_style="Caption", theme_text_color="Secondary",
        ))
        card.add_widget(MDLabel(
            text=skill.description, font_style="Caption",
            theme_text_color="Hint",
        ))
        return card
