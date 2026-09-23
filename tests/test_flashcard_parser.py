"""
Tasklyn — Flashcard Parser Tests
"""
import os, sys
import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from flashcards.parser import parse_text, ParseError, generate_example_markdown


VALID_MD_20 = """
# Deck: Test Deck
subject: Science

""" + "\n\n".join([f"## Q: Question {i}\nA: Answer {i}" for i in range(1, 21)])


def test_parse_valid_deck():
    deck = parse_text(VALID_MD_20)
    assert deck.name == "Test Deck"
    assert deck.subject == "Science"
    assert len(deck.cards) == 20


def test_parse_too_few_cards():
    short_md = "\n\n".join([f"## Q: Q{i}\nA: A{i}" for i in range(5)])
    with pytest.raises(ParseError, match="at least 20"):
        parse_text(short_md)


def test_parse_too_many_cards():
    long_md = "\n\n".join([f"## Q: Q{i}\nA: A{i}" for i in range(101)])
    with pytest.raises(ParseError, match="exceed 100"):
        parse_text(long_md)


def test_parse_missing_answer():
    bad = "\n\n".join([f"## Q: Q{i}\nA: A{i}" for i in range(19)])
    bad += "\n\n## Q: No answer here\n"
    with pytest.raises(ParseError, match="missing an 'A:'"):
        parse_text(bad)


def test_parse_mcq():
    mcq_block = """
## Q: Capital of France?
type: multiple_choice
- Berlin
- Rome
* Paris
- Madrid
A: Paris
"""
    base = "\n\n".join([f"## Q: Q{i}\nA: A{i}" for i in range(19)])
    deck = parse_text(base + "\n\n" + mcq_block)
    mcq_card = deck.cards[-1]
    assert mcq_card["q_type"] == "multiple_choice"
    assert "Paris" in mcq_card["choices"]
    assert mcq_card["answer"] == "Paris"


def test_parse_deck_color():
    md = "# Deck: ColorTest\ncolor: #FF5733\n\n"
    md += "\n\n".join([f"## Q: Q{i}\nA: A{i}" for i in range(20)])
    deck = parse_text(md)
    assert deck.color == "#FF5733"


def test_example_template_parseable():
    """The built-in template should fail gracefully (only 3 cards)."""
    tmpl = generate_example_markdown()
    with pytest.raises(ParseError):
        parse_text(tmpl)


def test_sanitize_script_injection():
    from utils.validation import sanitize_markdown
    evil = "<script>alert('xss')</script>Hello"
    clean = sanitize_markdown(evil)
    assert "<script>" not in clean
    assert "Hello" in clean


def test_identification_card_fields():
    md = "\n\n".join([f"## Q: Q{i}\nA: A{i}" for i in range(20)])
    deck = parse_text(md)
    for card in deck.cards:
        assert card["q_type"] == "identification"
        assert card["question"].startswith("Q")
        assert card["answer"].startswith("A")
