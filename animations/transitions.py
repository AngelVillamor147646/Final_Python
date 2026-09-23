"""
Tasklyn — Screen / Widget Animation Library
=============================================
Pure Kivy Animation helpers used for page transitions, card appear effects,
progress ring updates, and micro-animations.

All public functions are non-blocking: they return the ``Animation`` object
and schedule it immediately via ``anim.start(widget)``.
"""
from __future__ import annotations

from kivy.animation import Animation
from kivy.uix.widget import Widget


# ---------------------------------------------------------------------------
# Easing shorthands (Kivy uses string names)
# ---------------------------------------------------------------------------

EASE_IN_OUT  = "in_out_cubic"
EASE_OUT     = "out_cubic"
EASE_IN      = "in_cubic"
EASE_BOUNCE  = "out_bounce"
EASE_ELASTIC = "out_elastic"
EASE_LINEAR  = "linear"


# ---------------------------------------------------------------------------
# Fade transitions
# ---------------------------------------------------------------------------

def fade_in(widget: Widget, duration: float = 0.25) -> Animation:
    """Fade a widget from opacity=0 to opacity=1."""
    widget.opacity = 0
    anim = Animation(opacity=1, duration=duration, t=EASE_OUT)
    anim.start(widget)
    return anim


def fade_out(widget: Widget, duration: float = 0.2, on_complete=None) -> Animation:
    """Fade a widget from its current opacity to 0."""
    anim = Animation(opacity=0, duration=duration, t=EASE_IN)
    if on_complete:
        anim.bind(on_complete=on_complete)
    anim.start(widget)
    return anim


def fade_in_out(widget: Widget, hold: float = 1.5, fade: float = 0.3) -> Animation:
    """Fade in, hold, fade out — useful for toast messages."""
    anim = (
        Animation(opacity=1, duration=fade, t=EASE_OUT)
        + Animation(opacity=1, duration=hold)
        + Animation(opacity=0, duration=fade, t=EASE_IN)
    )
    anim.start(widget)
    return anim


# ---------------------------------------------------------------------------
# Slide transitions
# ---------------------------------------------------------------------------

def slide_in_from_right(widget: Widget, distance: float = 60, duration: float = 0.3) -> Animation:
    """Slide widget in from the right while fading in."""
    widget.x += distance
    widget.opacity = 0
    anim = Animation(x=widget.x - distance, opacity=1, duration=duration, t=EASE_OUT)
    anim.start(widget)
    return anim


def slide_in_from_bottom(widget: Widget, distance: float = 40, duration: float = 0.3) -> Animation:
    """Slide widget up from below while fading in."""
    widget.y -= distance
    widget.opacity = 0
    anim = Animation(y=widget.y + distance, opacity=1, duration=duration, t=EASE_OUT)
    anim.start(widget)
    return anim


def slide_out_to_left(widget: Widget, distance: float = 60, duration: float = 0.25, on_complete=None) -> Animation:
    """Slide widget out to the left while fading out."""
    anim = Animation(x=widget.x - distance, opacity=0, duration=duration, t=EASE_IN)
    if on_complete:
        anim.bind(on_complete=on_complete)
    anim.start(widget)
    return anim


# ---------------------------------------------------------------------------
# Scale / pop animations
# ---------------------------------------------------------------------------

def pop_in(widget: Widget, duration: float = 0.3) -> Animation:
    """Scale from 0 → 1.05 → 1.0 with a slight bounce."""
    widget.opacity = 0
    # Kivy doesn't have native scale, so we simulate via size
    # This is a simplified version — for true scale use ScatterLayout or canvas transform
    anim = Animation(opacity=1, duration=duration * 0.6, t=EASE_OUT)
    anim.start(widget)
    return anim


def pulse(widget: Widget, scale_delta: float = 0.05, duration: float = 0.15) -> Animation:
    """
    Quick scale pulse for XP/badge unlock feedback.
    Expands then contracts back to original size.
    """
    orig_w = widget.width
    orig_h = widget.height
    delta_w = orig_w * scale_delta
    delta_h = orig_h * scale_delta
    anim = (
        Animation(width=orig_w + delta_w, height=orig_h + delta_h,
                  x=widget.x - delta_w / 2, y=widget.y - delta_h / 2,
                  duration=duration, t=EASE_OUT)
        + Animation(width=orig_w, height=orig_h,
                    x=widget.x, y=widget.y,
                    duration=duration, t=EASE_IN)
    )
    anim.start(widget)
    return anim


# ---------------------------------------------------------------------------
# Progress / numeric animations
# ---------------------------------------------------------------------------

def animate_progress(
    widget: Widget,
    attr: str,
    target: float,
    duration: float = 0.5,
    t: str = EASE_OUT,
) -> Animation:
    """
    Smoothly animate a numeric property (e.g. ``value``, ``opacity``) to *target*.

    Parameters
    ----------
    widget:
        The Kivy widget to animate.
    attr:
        Name of the property to animate.
    target:
        Target value.
    duration:
        Animation duration in seconds.
    t:
        Easing transition name.
    """
    anim = Animation(**{attr: target}, duration=duration, t=t)
    anim.start(widget)
    return anim


# ---------------------------------------------------------------------------
# Card entrance stagger
# ---------------------------------------------------------------------------

def stagger_cards(widgets: list[Widget], delay_step: float = 0.08, duration: float = 0.3) -> None:
    """
    Animate a list of card widgets in with a staggered entrance effect.
    Each card fades and slides in with increasing delay.
    """
    from kivy.clock import Clock

    def _animate_card(widget: Widget, delay: float) -> None:
        def _start(_dt):
            slide_in_from_bottom(widget, distance=30, duration=duration)
        Clock.schedule_once(_start, delay)

    for i, widget in enumerate(widgets):
        widget.opacity = 0
        _animate_card(widget, i * delay_step)


# ---------------------------------------------------------------------------
# Shake (error feedback)
# ---------------------------------------------------------------------------

def shake(widget: Widget, amplitude: float = 8, duration: float = 0.4) -> Animation:
    """
    Horizontal shake animation for error feedback on a widget.
    """
    orig_x = widget.x
    step = duration / 6
    anim = (
        Animation(x=orig_x + amplitude, duration=step, t=EASE_OUT)
        + Animation(x=orig_x - amplitude, duration=step, t=EASE_IN_OUT)
        + Animation(x=orig_x + amplitude / 2, duration=step, t=EASE_IN_OUT)
        + Animation(x=orig_x - amplitude / 2, duration=step, t=EASE_IN_OUT)
        + Animation(x=orig_x + amplitude / 4, duration=step, t=EASE_IN_OUT)
        + Animation(x=orig_x, duration=step, t=EASE_OUT)
    )
    anim.start(widget)
    return anim


# ---------------------------------------------------------------------------
# Colour transition
# ---------------------------------------------------------------------------

def animate_colour(
    widget: Widget,
    attr: str,
    target_rgba: list[float],
    duration: float = 0.3,
) -> Animation:
    """Smoothly transition an RGBA colour property."""
    anim = Animation(**{attr: target_rgba}, duration=duration, t=EASE_OUT)
    anim.start(widget)
    return anim
