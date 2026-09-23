"""Flashcard service — deck/card CRUD, study sessions, markdown import."""
from __future__ import annotations
from typing import Optional
from database.repositories import (
    FlashcardDeckRepository, FlashcardRepository,
    FlashcardStudySessionRepository, SubjectRepository,
)
from models import Flashcard, FlashcardDeck, FlashcardStudySession
from utils.logger import get_logger
from utils.validation import validate_name

log = get_logger(__name__)
_deck_repo = FlashcardDeckRepository()
_card_repo = FlashcardRepository()
_session_repo = FlashcardStudySessionRepository()
_subj_repo = SubjectRepository()


# ── Decks ──────────────────────────────────────────────────────────────────

def get_decks(user_id: int) -> list[FlashcardDeck]:
    return _deck_repo.get_for_user(user_id)


def create_deck(user_id: int, name: str, subject_id=None,
                description="", color="#7C4DFF") -> tuple[bool, str, Optional[FlashcardDeck]]:
    ok, err = validate_name(name, "Deck name")
    if not ok:
        return False, err, None
    try:
        deck = _deck_repo.create(user_id, name.strip(), subject_id, description, color)
        return True, "", deck
    except Exception as exc:
        log.error("create_deck: %s", exc)
        return False, "Failed to create deck.", None


def delete_deck(deck_id: int) -> bool:
    _card_repo.delete_for_deck(deck_id)
    return _deck_repo.delete_by_id(deck_id)


def get_cards(deck_id: int, shuffled: bool = False) -> list[Flashcard]:
    return _card_repo.get_for_deck(deck_id, shuffled)


def add_card_to_deck(deck_id: int, question: str, answer: str) -> tuple[bool, str]:
    if not question.strip() or not answer.strip():
        return False, "Question and Answer cannot be empty."
    try:
        _card_repo.create(deck_id, question.strip(), answer.strip())
        _deck_repo.refresh_card_count(deck_id)
        return True, ""
    except Exception as exc:
        log.error("add_card_to_deck: %s", exc)
        return False, str(exc)


def get_mistake_cards(deck_id: int, user_id: int, limit: int = 20) -> list[Flashcard]:
    return _card_repo.get_mistakes(deck_id, user_id, limit)


# ── Markdown import ────────────────────────────────────────────────────────

def import_from_markdown(
    user_id: int, file_path: str,
    subject_id: Optional[int] = None,
) -> tuple[bool, str, Optional[FlashcardDeck]]:
    """Parse *file_path* and bulk-insert cards into a new deck."""
    from flashcards.parser import parse_file, ParseError
    try:
        parsed = parse_file(file_path)
        # Resolve subject from parsed metadata if not supplied
        if subject_id is None and parsed.subject:
            subj = _subj_repo.get_by_name(user_id, parsed.subject)
            if subj:
                subject_id = subj.id
        deck = _deck_repo.create(user_id, parsed.name, subject_id, "", parsed.color)
        count = _card_repo.bulk_create(deck.id, parsed.cards)
        _deck_repo.refresh_card_count(deck.id)
        # Award first_deck badge trigger
        from services.gamification_service import check_and_unlock_badges
        check_and_unlock_badges(user_id, trigger="flashcard_session")
        log.info("Imported %d cards into deck '%s'", count, parsed.name)
        return True, f"Imported {count} cards successfully.", deck
    except Exception as exc:
        log.error("import_from_markdown: %s", exc)
        return False, str(exc), None


# ── Study sessions ─────────────────────────────────────────────────────────

def start_study_session(user_id: int, deck_id: int) -> FlashcardStudySession:
    return _session_repo.create(user_id, deck_id)


def record_answer(session_id: int, flashcard_id: int, is_correct: bool) -> None:
    from database.connection import execute, commit
    execute(
        "INSERT INTO flashcard_results (session_id, flashcard_id, is_correct) VALUES (?,?,?)",
        (session_id, flashcard_id, 1 if is_correct else 0),
    )
    commit()


def close_study_session(session_id: int, user_id: int,
                         total: int, correct: int) -> tuple[float, list[str]]:
    """Close session; award XP; return (accuracy, unlocked_badge_slugs)."""
    _session_repo.close_session(session_id, total, correct)
    accuracy = correct / max(total, 1)
    from services.gamification_service import award_xp, check_and_unlock_badges
    from config import XP_FLASHCARD_CORRECT
    award_xp(user_id, "focus", correct * XP_FLASHCARD_CORRECT)
    badges = check_and_unlock_badges(user_id, trigger="flashcard_session")
    from services.streak_service import record_activity
    record_activity(user_id)
    return accuracy, badges


def get_study_history(user_id: int, limit: int = 30) -> list[FlashcardStudySession]:
    return _session_repo.get_history(user_id, limit)


def get_average_accuracy(user_id: int, start: str, end: str) -> float:
    return _session_repo.average_accuracy(user_id, start, end)


def get_subjects(user_id: int):
    return _subj_repo.get_for_user(user_id)
