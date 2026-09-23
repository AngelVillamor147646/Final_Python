"""
Tasklyn — Theme Manager
=========================
Provides a global ``ThemeManager`` singleton that:
  • Stores the current theme name ("Dark" | "Light")
  • Exposes token dicts for the active theme
  • Applies the theme to the running KivyMD app
  • Persists the user preference via the settings repository
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Any

from themes.color_tokens import DARK, LIGHT, TYPOGRAPHY, SPACING, RADIUS, DURATION, LABEL_COLOURS, PRIORITY_COLOURS

if TYPE_CHECKING:
    from kivymd.app import MDApp


class ThemeManager:
    """
    Singleton theme manager.

    Usage
    -----
    >>> tm = ThemeManager.instance()
    >>> tm.set_theme("Light")
    >>> bg = tm.tokens["bg_primary"]
    """

    _instance: "ThemeManager | None" = None

    def __init__(self) -> None:
        self._theme: str = "Dark"
        self._tokens: dict[str, Any] = DARK.copy()

    # ------------------------------------------------------------------
    # Singleton
    # ------------------------------------------------------------------

    @classmethod
    def instance(cls) -> "ThemeManager":
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    @property
    def theme(self) -> str:
        """Current theme name: ``'Dark'`` or ``'Light'``."""
        return self._theme

    @property
    def tokens(self) -> dict[str, Any]:
        """Active token dict for the current theme."""
        return self._tokens

    @property
    def is_dark(self) -> bool:
        return self._theme == "Dark"

    def set_theme(self, theme: str, app: "MDApp | None" = None) -> None:
        """
        Switch to *theme* (``'Dark'`` or ``'Light'``).

        Optionally pass the running *app* to apply the theme immediately.
        """
        if theme not in ("Dark", "Light"):
            raise ValueError(f"Unknown theme: {theme!r}")
        self._theme = theme
        self._tokens = DARK.copy() if theme == "Dark" else LIGHT.copy()
        if app is not None:
            self._apply_to_app(app)

    def toggle(self, app: "MDApp | None" = None) -> str:
        """Toggle between Dark and Light; return new theme name."""
        new = "Light" if self._theme == "Dark" else "Dark"
        self.set_theme(new, app)
        return new

    def colour(self, key: str, fallback: str = "#FFFFFF") -> str:
        """Return a hex colour from the active token set."""
        return self._tokens.get(key, fallback)

    def kivy_colour(self, key: str) -> list[float]:
        """Return a Kivy RGBA list for a theme token key."""
        from utils.helpers import hex_to_kivy_colour
        return hex_to_kivy_colour(self.colour(key))

    # ------------------------------------------------------------------
    # Shared accessors (theme-independent)
    # ------------------------------------------------------------------

    @staticmethod
    def typography() -> dict:
        return TYPOGRAPHY

    @staticmethod
    def spacing() -> dict:
        return SPACING

    @staticmethod
    def radius() -> dict:
        return RADIUS

    @staticmethod
    def duration() -> dict:
        return DURATION

    @staticmethod
    def label_colours() -> list[str]:
        return LABEL_COLOURS

    @staticmethod
    def priority_colour(priority: str) -> str:
        return PRIORITY_COLOURS.get(priority.lower(), "#9E9EBF")

    # ------------------------------------------------------------------
    # Private
    # ------------------------------------------------------------------

    def _apply_to_app(self, app: "MDApp") -> None:
        """Apply KivyMD palette and style to a running MDApp instance."""
        tokens = self._tokens
        app.theme_cls.primary_palette = tokens["md_primary"]
        app.theme_cls.accent_palette = tokens["md_accent"]
        app.theme_cls.theme_style = tokens["md_theme"]


# Module-level convenience alias
theme_manager = ThemeManager.instance()
