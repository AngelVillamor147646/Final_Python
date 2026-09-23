"""
Tasklyn — Flashcards Screen
=============================
Deck management, markdown import, card study with MCQ + identification,
mistake repetition, score tracking, and accuracy display.
"""
from __future__ import annotations
from kivy.clock import Clock
from kivy.lang import Builder
from kivy.metrics import dp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDFlatButton, MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from utils.helpers import TasklynSnackbar as Snackbar

Builder.load_string("""
<FlashcardScreen>:
    name: 'flashcards'
    MDBoxLayout:
        orientation: 'vertical'

        MDTopAppBar:
            title: 'Flashcards'
            elevation: 0
            right_action_items: [['file-import', lambda x: root.open_import_dialog()], ['plus-circle', lambda x: root.open_create_deck_dialog()]]

        MDScrollView:
            MDBoxLayout:
                id: deck_list
                orientation: 'vertical'
                padding: dp(12)
                spacing: dp(10)
                size_hint_y: None
                height: self.minimum_height
""")


class FlashcardScreen(MDScreen):
    def __init__(self, user_id: int, **kwargs):
        super().__init__(**kwargs)
        self.user_id = user_id
        self._dialog = None
        Clock.schedule_once(self._refresh)

    def on_enter(self):
        self._refresh()

    def _refresh(self, *_):
        from services.flashcard_service import get_decks
        decks = get_decks(self.user_id)
        box = self.ids.deck_list
        box.clear_widgets()
        if not decks:
            box.add_widget(MDLabel(text="No flashcard decks yet.\nImport a Markdown file or create a deck.",
                                   halign="center", theme_text_color="Hint",
                                   font_style="Body2", size_hint_y=None, height=dp(80)))
        for deck in decks:
            card = self._make_deck_card(deck)
            box.add_widget(card)

    def _make_deck_card(self, deck) -> MDCard:
        from utils.helpers import hex_to_kivy_colour
        card = MDCard(orientation="horizontal", padding=[dp(14), dp(12)],
                      spacing=dp(12), size_hint_y=None, height=dp(80),
                      elevation=3, radius=[dp(14)])
        with card.canvas.before:
            from kivy.graphics import Color, RoundedRectangle
            Color(*hex_to_kivy_colour(deck.color))
            RoundedRectangle(pos=(card.x, card.y + dp(6)),
                             size=(dp(4), dp(68)), radius=[dp(4)])
        col = MDBoxLayout(orientation="vertical")
        col.add_widget(MDLabel(text=f"[b]{deck.name}[/b]", markup=True,
                               font_style="Subtitle1"))
        col.add_widget(MDLabel(text=f"{deck.card_count} cards",
                               theme_text_color="Secondary", font_style="Caption"))
        card.add_widget(col)

        btn_row = MDBoxLayout(orientation="horizontal", spacing=dp(4),
                               size_hint=(None, 1), width=dp(130))
        add_btn   = MDIconButton(icon="plus", icon_size="22sp",
                                  on_release=lambda *_, did=deck.id: self.open_add_card_dialog(did))
        study_btn = MDIconButton(icon="play-circle", icon_size="22sp",
                                  on_release=lambda *_, did=deck.id: self._start_study(did))
        del_btn   = MDIconButton(icon="delete-outline", icon_size="18sp",
                                  on_release=lambda *_, did=deck.id: self._delete_deck(did))
        btn_row.add_widget(add_btn)
        btn_row.add_widget(study_btn)
        btn_row.add_widget(del_btn)
        card.add_widget(btn_row)
        return card

    # ── Deck creation ─────────────────────────────────────────────────────

    def open_create_deck_dialog(self):
        content = MDBoxLayout(orientation="vertical", spacing=dp(8),
                               size_hint_y=None, height=dp(160), padding=[dp(4)]*4)
        self._d_name = MDTextField(hint_text="Deck name *")
        self._d_desc = MDTextField(hint_text="Description")
        content.add_widget(self._d_name)
        content.add_widget(self._d_desc)
        self._dialog = MDDialog(
            title="New Flashcard Deck", type="custom", content_cls=content,
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda *_: self._dialog.dismiss()),
                MDRaisedButton(text="CREATE", on_release=self._save_deck),
            ],
        )
        self._dialog.open()

    def _save_deck(self, *_):
        from services.flashcard_service import create_deck
        ok, err, deck = create_deck(self.user_id, self._d_name.text,
                                     description=self._d_desc.text)
        if ok:
            self._dialog.dismiss()
            self._refresh()
            Snackbar(text="Deck created!").open()
        else:
            Snackbar(text=err).open()

    # ── Card creation ─────────────────────────────────────────────────────

    def open_add_card_dialog(self, deck_id: int):
        content = MDBoxLayout(orientation="vertical", spacing=dp(8),
                               size_hint_y=None, height=dp(160), padding=[dp(4)]*4)
        self._c_quest = MDTextField(hint_text="Question *")
        self._c_ans = MDTextField(hint_text="Answer *")
        content.add_widget(self._c_quest)
        content.add_widget(self._c_ans)
        self._dialog = MDDialog(
            title="Add Flashcard", type="custom", content_cls=content,
            buttons=[
                MDFlatButton(text="CANCEL", on_release=lambda *_: self._dialog.dismiss()),
                MDRaisedButton(text="ADD", on_release=lambda *_: self._save_card(deck_id)),
            ],
        )
        self._dialog.open()

    def _save_card(self, deck_id: int):
        from services.flashcard_service import add_card_to_deck
        ok, err = add_card_to_deck(deck_id, self._c_quest.text, self._c_ans.text)
        if ok:
            self._dialog.dismiss()
            self._refresh()
            Snackbar(text="Card added!").open()
        else:
            Snackbar(text=err).open()

    # ── Markdown import ───────────────────────────────────────────────────

    def open_import_dialog(self):
        content = MDBoxLayout(orientation="vertical", spacing=dp(8),
                               size_hint_y=None, height=dp(100), padding=[dp(4)]*4)
        self._import_path = MDTextField(hint_text="Path to .md file")
        content.add_widget(self._import_path)
        self._dialog = MDDialog(
            title="Import Flashcards", type="custom", content_cls=content,
            buttons=[
                MDFlatButton(text="TEMPLATE",
                              on_release=lambda *_: self._show_template()),
                MDFlatButton(text="CANCEL", on_release=lambda *_: self._dialog.dismiss()),
                MDRaisedButton(text="IMPORT", on_release=self._do_import),
            ],
        )
        self._dialog.open()

    def _do_import(self, *_):
        from services.flashcard_service import import_from_markdown
        ok, msg, deck = import_from_markdown(self.user_id, self._import_path.text)
        self._dialog.dismiss()
        Snackbar(text=msg).open()
        if ok:
            self._refresh()

    def _show_template(self):
        from flashcards.parser import generate_example_markdown
        tmpl = generate_example_markdown()
        dlg = MDDialog(
            title="Markdown Template",
            text=tmpl[:800],
            buttons=[MDFlatButton(text="CLOSE", on_release=lambda *_: dlg.dismiss())],
        )
        dlg.open()

    # ── Study session ─────────────────────────────────────────────────────

    def _start_study(self, deck_id: int):
        from services.flashcard_service import get_cards, start_study_session
        cards = get_cards(deck_id, shuffled=True)
        if not cards:
            Snackbar(text="This deck has no cards.").open()
            return
        session = start_study_session(self.user_id, deck_id)
        self._run_study(session, cards)

    def _run_study(self, session, cards: list):
        self._study_session  = session
        self._study_cards    = cards
        self._study_index    = 0
        self._study_correct  = 0
        self._study_incorrect = 0
        self._show_card()

    def _show_card(self):
        if self._study_index >= len(self._study_cards):
            self._finish_study()
            return
        card = self._study_cards[self._study_index]
        self._current_card = card

        import json
        choices = json.loads(card.choices) if card.q_type == "multiple_choice" else []

        content = MDBoxLayout(orientation="vertical", spacing=dp(12),
                               size_hint_y=None, padding=[dp(4)]*4)
        content.height = dp(360) if choices else dp(260)
        content.add_widget(MDLabel(
            text=f"Q {self._study_index + 1} / {len(self._study_cards)}",
            theme_text_color="Secondary", font_style="Caption",
            size_hint_y=None, height=dp(20),
        ))
        content.add_widget(MDLabel(
            text=card.question, font_style="Subtitle1",
            size_hint_y=None, height=dp(80),
        ))

        if card.q_type == "multiple_choice" and choices:
            for choice in choices:
                btn = MDFlatButton(text=choice, size_hint_y=None, height=dp(40),
                                   on_release=lambda *_, c=choice: self._answer_mcq(c))
                content.add_widget(btn)
        else:
            self._answer_field = MDTextField(hint_text="Your answer…",
                                              size_hint_y=None, height=dp(48))
            content.add_widget(self._answer_field)

        dlg_btns = []
        if card.q_type == "identification":
            dlg_btns = [
                MDFlatButton(text="SKIP",   on_release=lambda *_: self._answer_id("__skip__")),
                MDRaisedButton(text="CHECK", on_release=lambda *_: self._answer_id(
                    getattr(self, "_answer_field", None) and self._answer_field.text or "")),
            ]

        self._study_dlg = MDDialog(
            title="Study Session", type="custom",
            content_cls=content, buttons=dlg_btns,
        )
        self._study_dlg.open()

    def _answer_mcq(self, choice: str):
        correct = choice.strip().lower() == self._current_card.answer.strip().lower()
        self._record_and_advance(correct)

    def _answer_id(self, user_ans: str):
        correct = user_ans.strip().lower() == self._current_card.answer.strip().lower()
        self._record_and_advance(correct)

    def _record_and_advance(self, correct: bool):
        from services.flashcard_service import record_answer
        if correct:
            self._study_correct += 1
        else:
            self._study_incorrect += 1
        record_answer(self._study_session.id, self._current_card.id, correct)
        self._study_dlg.dismiss()
        Snackbar(text="Correct!" if correct else f"Answer: {self._current_card.answer}").open()
        self._study_index += 1
        Clock.schedule_once(lambda *_: self._show_card(), 0.6)

    def _finish_study(self):
        from services.flashcard_service import close_study_session
        from kivymd.uix.gridlayout import MDGridLayout
        from views.widgets import StatCard
        
        total = self._study_correct + self._study_incorrect
        acc, badges = close_study_session(self._study_session.id, self.user_id,
                                           total, self._study_correct)
        
        content = MDBoxLayout(orientation="vertical", spacing=dp(16),
                               size_hint_y=None, height=dp(160), padding=[dp(8)]*4)
        content.add_widget(MDLabel(text="Session Complete!", font_style="H5",
                                   halign="center", size_hint_y=None, height=dp(40)))
                                   
        grid = MDGridLayout(cols=3, spacing=dp(10), size_hint_y=None)
        grid.bind(minimum_height=grid.setter('height'))
        
        grid.add_widget(StatCard(icon="check-circle-outline", title="Correct", 
                                 value=str(self._study_correct), accent_color=[0.4, 0.74, 0.42, 1]))
        grid.add_widget(StatCard(icon="close-circle-outline", title="Incorrect", 
                                 value=str(self._study_incorrect), accent_color=[0.85, 0.3, 0.3, 1]))
        grid.add_widget(StatCard(icon="target", title="Accuracy", 
                                 value=f"{acc*100:.0f}%", accent_color=[0.49, 0.30, 1, 1]))
        
        content.add_widget(grid)

        dlg = MDDialog(
            type="custom", content_cls=content,
            buttons=[MDFlatButton(text="DONE", on_release=lambda *_: dlg.dismiss())],
        )
        dlg.open()
        if badges:
            Clock.schedule_once(
                lambda *_: Snackbar(text=f"Badge: {badges[0]}").open(), 1.5)

    def _delete_deck(self, deck_id: int):
        from services.flashcard_service import delete_deck
        delete_deck(deck_id)
        self._refresh()
        Snackbar(text="Deck deleted.").open()
