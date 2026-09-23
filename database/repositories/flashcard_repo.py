"""Flashcard deck and card repositories."""
from __future__ import annotations
import sqlite3
from typing import Optional
from database.repositories.base import BaseRepository
from models import Flashcard, FlashcardDeck, FlashcardStudySession, FlashcardResult


class FlashcardDeckRepository(BaseRepository[FlashcardDeck]):
    TABLE = "flashcard_decks"

    def _row_to_model(self, row: sqlite3.Row) -> FlashcardDeck:
        return FlashcardDeck(
            id=row["id"], user_id=row["user_id"], name=row["name"],
            subject_id=row["subject_id"], description=row["description"] or "",
            color=row["color"] or "#7C4DFF", card_count=row["card_count"] or 0,
            created_at=row["created_at"], updated_at=row["updated_at"],
        )

    def create(self, user_id: int, name: str, subject_id: Optional[int] = None,
               description: str = "", color: str = "#7C4DFF") -> FlashcardDeck:
        row_id = self._insert({
            "user_id": user_id, "name": name, "subject_id": subject_id,
            "description": description, "color": color,
        })
        return self.get_by_id(row_id)  # type: ignore[return-value]

    def update(self, deck_id: int, name: str, subject_id: Optional[int],
               description: str, color: str) -> bool:
        cur = self._execute(
            """UPDATE flashcard_decks SET name=?, subject_id=?,
               description=?, color=?,
               updated_at=datetime('now','localtime') WHERE id=?""",
            (name, subject_id, description, color, deck_id),
        )
        self._commit()
        return cur.rowcount > 0

    def refresh_card_count(self, deck_id: int) -> None:
        self._execute(
            """UPDATE flashcard_decks SET card_count=(
               SELECT COUNT(*) FROM flashcards WHERE deck_id=?)
               WHERE id=?""",
            (deck_id, deck_id),
        )
        self._commit()

    def get_for_user(self, user_id: int) -> list[FlashcardDeck]:
        rows = self._fetchall(
            "SELECT * FROM flashcard_decks WHERE user_id=? ORDER BY name",
            (user_id,),
        )
        return self._rows_to_models(rows)


class FlashcardRepository(BaseRepository[Flashcard]):
    TABLE = "flashcards"

    def _row_to_model(self, row: sqlite3.Row) -> Flashcard:
        return Flashcard(
            id=row["id"], deck_id=row["deck_id"],
            question=row["question"], answer=row["answer"],
            q_type=row["q_type"], choices=row["choices"] or "[]",
            tags=row["tags"] or "[]", difficulty=row["difficulty"] or 1,
            sort_order=row["sort_order"] or 0, created_at=row["created_at"],
        )

    def create(self, deck_id: int, question: str, answer: str,
               q_type: str = "identification", choices: str = "[]",
               tags: str = "[]", difficulty: int = 1) -> Flashcard:
        row_id = self._insert({
            "deck_id": deck_id, "question": question, "answer": answer,
            "q_type": q_type, "choices": choices, "tags": tags,
            "difficulty": difficulty,
        })
        return self.get_by_id(row_id)  # type: ignore[return-value]

    def bulk_create(self, deck_id: int, cards: list[dict]) -> int:
        """Insert many cards at once; return count inserted."""
        from database.connection import executemany, commit
        rows = [
            (deck_id, c["question"], c["answer"], c.get("q_type", "identification"),
             c.get("choices", "[]"), c.get("tags", "[]"), c.get("difficulty", 1))
            for c in cards
        ]
        executemany(
            """INSERT INTO flashcards
               (deck_id, question, answer, q_type, choices, tags, difficulty)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            rows,
        )
        commit()
        return len(rows)

    def get_for_deck(self, deck_id: int, shuffled: bool = False) -> list[Flashcard]:
        order = "RANDOM()" if shuffled else "sort_order, id"
        rows = self._fetchall(
            f"SELECT * FROM flashcards WHERE deck_id=? ORDER BY {order}",
            (deck_id,),
        )
        return self._rows_to_models(rows)

    def get_mistakes(self, deck_id: int, user_id: int, limit: int = 20) -> list[Flashcard]:
        """Cards most frequently answered incorrectly."""
        rows = self._fetchall(
            """SELECT f.*, COUNT(r.id) AS err_count
               FROM flashcards f
               JOIN flashcard_results r ON r.flashcard_id = f.id
               JOIN flashcard_study_sessions s ON r.session_id = s.id
               WHERE f.deck_id=? AND s.user_id=? AND r.is_correct=0
               GROUP BY f.id ORDER BY err_count DESC LIMIT ?""",
            (deck_id, user_id, limit),
        )
        return self._rows_to_models(rows)

    def delete_for_deck(self, deck_id: int) -> int:
        cur = self._execute("DELETE FROM flashcards WHERE deck_id=?", (deck_id,))
        self._commit()
        return cur.rowcount


class FlashcardStudySessionRepository(BaseRepository[FlashcardStudySession]):
    TABLE = "flashcard_study_sessions"

    def _row_to_model(self, row: sqlite3.Row) -> FlashcardStudySession:
        return FlashcardStudySession(
            id=row["id"], user_id=row["user_id"], deck_id=row["deck_id"],
            started_at=row["started_at"], ended_at=row["ended_at"],
            total_cards=row["total_cards"] or 0, correct=row["correct"] or 0,
            incorrect=row["incorrect"] or 0, accuracy=row["accuracy"] or 0.0,
        )

    def create(self, user_id: int, deck_id: int) -> FlashcardStudySession:
        row_id = self._insert({"user_id": user_id, "deck_id": deck_id})
        return self.get_by_id(row_id)  # type: ignore[return-value]

    def close_session(self, session_id: int, total: int, correct: int) -> bool:
        accuracy = round(correct / total, 4) if total > 0 else 0.0
        cur = self._execute(
            """UPDATE flashcard_study_sessions SET
               ended_at=datetime('now','localtime'), total_cards=?,
               correct=?, incorrect=?, accuracy=? WHERE id=?""",
            (total, correct, total - correct, accuracy, session_id),
        )
        self._commit()
        return cur.rowcount > 0

    def get_history(self, user_id: int, limit: int = 30) -> list[FlashcardStudySession]:
        rows = self._fetchall(
            """SELECT * FROM flashcard_study_sessions
               WHERE user_id=? ORDER BY started_at DESC LIMIT ?""",
            (user_id, limit),
        )
        return self._rows_to_models(rows)

    def average_accuracy(self, user_id: int, start: str, end: str) -> float:
        row = self._fetchone(
            """SELECT COALESCE(AVG(accuracy), 0) AS avg_acc
               FROM flashcard_study_sessions
               WHERE user_id=? AND ended_at IS NOT NULL
               AND date(started_at) BETWEEN ? AND ?""",
            (user_id, start, end),
        )
        return row["avg_acc"] if row else 0.0

    def total_correct(self, user_id: int) -> int:
        row = self._fetchone(
            "SELECT COALESCE(SUM(correct), 0) AS n FROM flashcard_study_sessions WHERE user_id=?",
            (user_id,),
        )
        return row["n"] if row else 0

    def add_result(self, session_id: int, flashcard_id: int, is_correct: bool) -> None:
        from database.connection import execute, commit
        execute(
            """INSERT INTO flashcard_results (session_id, flashcard_id, is_correct)
               VALUES (?, ?, ?)""",
            (session_id, flashcard_id, 1 if is_correct else 0),
        )
        commit()
