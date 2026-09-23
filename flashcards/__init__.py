"""Flashcards package."""
from flashcards.parser import parse_text, parse_file, generate_example_markdown, ParseError
__all__ = ["parse_text", "parse_file", "generate_example_markdown", "ParseError"]
