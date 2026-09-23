"""
Tasklyn — Design Token Definitions
=====================================
Single source of truth for all colour, spacing, typography, and shape
tokens used by the dark and light theme modules.  KivyMD palette names
are mapped here alongside raw hex values for canvas drawing.
"""
from __future__ import annotations

# ---------------------------------------------------------------------------
# Brand / primary colours
# ---------------------------------------------------------------------------

PRIMARY_PURPLE     = "#7C4DFF"   # Main brand purple (500)
PRIMARY_PURPLE_700 = "#5E35B1"
PRIMARY_PURPLE_300 = "#B39DDB"
PRIMARY_PURPLE_100 = "#EDE7F6"

ACCENT_AMBER       = "#FFB300"
ACCENT_AMBER_700   = "#FF8F00"

# ---------------------------------------------------------------------------
# Subject / label colour palette (10 distinct colours)
# ---------------------------------------------------------------------------

LABEL_COLOURS: list[str] = [
    "#EF5350",   # Red
    "#42A5F5",   # Blue
    "#66BB6A",   # Green
    "#FFA726",   # Orange
    "#AB47BC",   # Purple
    "#26C6DA",   # Cyan
    "#EC407A",   # Pink
    "#8D6E63",   # Brown
    "#78909C",   # Blue-Grey
    "#26A69A",   # Teal
]

# ---------------------------------------------------------------------------
# Priority colours
# ---------------------------------------------------------------------------

PRIORITY_COLOURS: dict[str, str] = {
    "low":      "#4CAF50",
    "medium":   "#FF9800",
    "high":     "#F44336",
    "critical": "#9C27B0",
}

# ---------------------------------------------------------------------------
# Dark theme tokens
# ---------------------------------------------------------------------------

DARK = {
    # Backgrounds
    "bg_primary":      "#121212",
    "bg_secondary":    "#1E1E2E",
    "bg_card":         "#252536",
    "bg_elevated":     "#2E2E4A",
    "bg_input":        "#1A1A2E",

    # Text
    "text_primary":    "#E8E8FF",
    "text_secondary":  "#9E9EBF",
    "text_disabled":   "#5A5A7A",
    "text_on_primary": "#FFFFFF",

    # Accents
    "primary":         PRIMARY_PURPLE,
    "primary_dark":    PRIMARY_PURPLE_700,
    "primary_light":   PRIMARY_PURPLE_300,
    "accent":          ACCENT_AMBER,

    # Semantic
    "success":         "#4CAF50",
    "warning":         "#FF9800",
    "error":           "#EF5350",
    "info":            "#42A5F5",

    # UI chrome
    "divider":         "#2E2E4A",
    "ripple":          "#FFFFFF1A",
    "overlay":         "#00000080",
    "shadow":          "#00000060",

    # Bottom nav
    "nav_bg":          "#1A1A2E",
    "nav_active":      PRIMARY_PURPLE,
    "nav_inactive":    "#5A5A7A",

    # KivyMD palette name
    "md_primary":      "DeepPurple",
    "md_accent":       "Amber",
    "md_theme":        "Dark",
}

# ---------------------------------------------------------------------------
# Light theme tokens
# ---------------------------------------------------------------------------

LIGHT = {
    "bg_primary":      "#F8F7FF",
    "bg_secondary":    "#FFFFFF",
    "bg_card":         "#FFFFFF",
    "bg_elevated":     "#EDE7F6",
    "bg_input":        "#F3F0FF",

    "text_primary":    "#1A1A2E",
    "text_secondary":  "#4A4A6A",
    "text_disabled":   "#9E9EBF",
    "text_on_primary": "#FFFFFF",

    "primary":         PRIMARY_PURPLE,
    "primary_dark":    PRIMARY_PURPLE_700,
    "primary_light":   PRIMARY_PURPLE_100,
    "accent":          ACCENT_AMBER,

    "success":         "#388E3C",
    "warning":         "#F57C00",
    "error":           "#D32F2F",
    "info":            "#1976D2",

    "divider":         "#E0D9FF",
    "ripple":          "#7C4DFF1A",
    "overlay":         "#00000040",
    "shadow":          "#00000020",

    "nav_bg":          "#FFFFFF",
    "nav_active":      PRIMARY_PURPLE,
    "nav_inactive":    "#9E9EBF",

    "md_primary":      "DeepPurple",
    "md_accent":       "Amber",
    "md_theme":        "Light",
}

# ---------------------------------------------------------------------------
# Typography
# ---------------------------------------------------------------------------

TYPOGRAPHY = {
    "h1":        {"size": 32, "weight": "Bold"},
    "h2":        {"size": 24, "weight": "Bold"},
    "h3":        {"size": 20, "weight": "Medium"},
    "h4":        {"size": 18, "weight": "Medium"},
    "body_lg":   {"size": 16, "weight": "Regular"},
    "body_md":   {"size": 14, "weight": "Regular"},
    "body_sm":   {"size": 12, "weight": "Regular"},
    "caption":   {"size": 11, "weight": "Regular"},
    "overline":  {"size": 10, "weight": "Medium"},
    "button":    {"size": 14, "weight": "Medium"},
    "mono":      {"size": 13, "weight": "Regular"},
}

# ---------------------------------------------------------------------------
# Spacing scale (dp)
# ---------------------------------------------------------------------------

SPACING = {
    "xs":  4,
    "sm":  8,
    "md": 16,
    "lg": 24,
    "xl": 32,
    "2xl":48,
}

# ---------------------------------------------------------------------------
# Shape / corner radius (dp)
# ---------------------------------------------------------------------------

RADIUS = {
    "none":   0,
    "sm":     4,
    "md":     8,
    "lg":    16,
    "xl":    24,
    "full":  50,
}

# ---------------------------------------------------------------------------
# Elevation / shadow levels
# ---------------------------------------------------------------------------

ELEVATION = {
    "flat":   0,
    "raised": 2,
    "card":   4,
    "modal":  8,
    "dialog":16,
}

# ---------------------------------------------------------------------------
# Animation durations (seconds)
# ---------------------------------------------------------------------------

DURATION = {
    "instant":   0.0,
    "fast":      0.15,
    "normal":    0.25,
    "slow":      0.4,
    "very_slow": 0.6,
}
