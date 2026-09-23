"""
Tasklyn — Flashcard Markdown Parser
======================================
Parses a Markdown file into a list of card dicts ready for bulk DB insert.

Supported format
----------------

    # Deck: My Deck Name
    subject: Mathematics
    color: #42A5F5

    ---

    ## Q: What is the quadratic formula?
    A: x = (-b ± √(b²-4ac)) / 2a

    ---

    ## Q: Which of the following is a prime number?
    type: multiple_choice
    - 4
    - 6
    * 7
    - 9
    A: 7

Rules:
- Identification cards: ``## Q:`` … ``A:``
- Multiple choice: add ``type: multiple_choice``, list items with ``-`` (wrong) or ``*`` (correct)
- Answer line must start with ``A:``
- 20–100 cards per deck
"""
from __future__ import annotations
import re
from pathlib import Path
from typing import Optional

from utils.logger import get_logger
from utils.validation import sanitize_markdown, validate_card_count

log = get_logger(__name__)


class ParseError(ValueError):
    """Raised when the Markdown source is structurally invalid."""


# ── Regex patterns ─────────────────────────────────────────────────────────
_DECK_RE    = re.compile(r"^#\s*Deck:\s*(.+)$", re.MULTILINE)
_SUBJECT_RE = re.compile(r"^subject:\s*(.+)$",  re.MULTILINE | re.IGNORECASE)
_COLOR_RE   = re.compile(r"^color:\s*(#[0-9A-Fa-f]{3,6})$", re.MULTILINE | re.IGNORECASE)
_Q_RE       = re.compile(r"^#{1,3}\s*Q:\s*(.+)$", re.MULTILINE)
_A_RE       = re.compile(r"^A:\s*(.+)$",          re.MULTILINE)
_TYPE_RE    = re.compile(r"^type:\s*(\w+)$",      re.MULTILINE | re.IGNORECASE)
_WRONG_RE   = re.compile(r"^-\s+(.+)$",           re.MULTILINE)
_RIGHT_RE   = re.compile(r"^\*\s+(.+)$",          re.MULTILINE)


class ParsedDeck:
    def __init__(self):
        self.name: str = "Imported Deck"
        self.subject: Optional[str] = None
        self.color: str = "#7C4DFF"
        self.cards: list[dict] = []


def parse_file(path: str | Path) -> ParsedDeck:
    """Parse a Markdown flashcard file; raise ParseError on invalid input."""
    path = Path(path)
    if not path.exists():
        raise ParseError(f"File not found: {path}")
    text = path.read_text(encoding="utf-8")
    return parse_text(text)


def parse_text(text: str) -> ParsedDeck:
    """Parse raw Markdown text; raise ParseError on invalid input."""
    text = sanitize_markdown(text)
    deck = ParsedDeck()

    # Extract deck-level metadata
    m = _DECK_RE.search(text)
    if m:
        deck.name = m.group(1).strip()

    m = _SUBJECT_RE.search(text)
    if m:
        deck.subject = m.group(1).strip()

    m = _COLOR_RE.search(text)
    if m:
        deck.color = m.group(1).strip()

    # Split into card blocks by horizontal rule or Q: header
    # Strategy: find every Q: header position and slice
    q_positions = [(m.start(), m.group(1).strip()) for m in _Q_RE.finditer(text)]
    if not q_positions:
        raise ParseError("No questions found. Use '## Q: <question>' for each card.")

    for i, (pos, question) in enumerate(q_positions):
        # Slice the block from this Q to the next Q (or end of text)
        end = q_positions[i + 1][0] if i + 1 < len(q_positions) else len(text)
        block = text[pos:end]

        # Determine type
        t_match = _TYPE_RE.search(block)
        q_type = "multiple_choice" if (t_match and "multiple" in t_match.group(1).lower()) else "identification"

        # Extract answer
        a_match = _A_RE.search(block)
        if not a_match:
            raise ParseError(f"Card #{i+1} (Q: {question[:40]}) is missing an 'A:' answer line.")
        answer = a_match.group(1).strip()

        card: dict = {
            "question": question,
            "answer":   answer,
            "q_type":   q_type,
            "choices":  "[]",
            "tags":     "[]",
            "difficulty": 1,
        }

        if q_type == "multiple_choice":
            wrong = [m.group(1).strip() for m in _WRONG_RE.finditer(block)]
            right = [m.group(1).strip() for m in _RIGHT_RE.finditer(block)]
            all_choices = wrong + right
            if not all_choices:
                raise ParseError(
                    f"Card #{i+1} (MCQ): No choices found. "
                    "Use '- wrong' and '* correct' for options."
                )
            if not right:
                raise ParseError(f"Card #{i+1} (MCQ): No correct choice marked with '*'.")
            import json
            card["choices"] = json.dumps(all_choices)
            card["answer"] = right[0]   # canonical answer = first starred item

        deck.cards.append(card)

    # Validate count
    ok, err = validate_card_count(len(deck.cards))
    if not ok:
        raise ParseError(err)

    log.info("Parsed deck '%s' with %d cards.", deck.name, len(deck.cards))
    return deck


def generate_example_markdown() -> str:
    """Return a sample Markdown template for user reference."""
    return """\
# Deck: Sample Deck
subject: General Science
color: #42A5F5

---

## Q: What is the chemical symbol for water?
A: H2O

---

## Q: Which planet is closest to the Sun?
type: multiple_choice
- Earth
- Mars
* Mercury
- Venus
A: Mercury

---

## Q: What is Newton's First Law?
A: An object at rest stays at rest unless acted on by an external force.
"""
