"""Tasklyn — Domain Models (dataclasses for every table)."""
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional


@dataclass
class User:
    id: int
    name: str
    avatar_id: str = "boy_neutral"
    gender: str = "boy"
    created_at: str = ""
    updated_at: str = ""


@dataclass
class Subject:
    id: int
    user_id: int
    name: str
    color: str = "#7C4DFF"
    instructor: str = ""
    room: str = ""
    created_at: str = ""


@dataclass
class Task:
    id: int
    user_id: int
    title: str
    subject_id: Optional[int] = None
    description: str = ""
    priority: str = "medium"
    status: str = "pending"
    label_color: str = "#7C4DFF"
    deadline: Optional[str] = None
    reminder_at: Optional[str] = None
    is_recurring: bool = False
    recur_rule: Optional[str] = None
    parent_task_id: Optional[int] = None
    sort_order: int = 0
    completed_at: Optional[str] = None
    created_at: str = ""
    updated_at: str = ""


@dataclass
class Schedule:
    id: int
    user_id: int
    title: str
    day_of_week: int
    start_time: str
    end_time: str
    subject_id: Optional[int] = None
    room: str = ""
    instructor: str = ""
    color: str = "#7C4DFF"
    reminder_minutes: int = 15
    is_active: bool = True
    created_at: str = ""


@dataclass
class PomodoroSession:
    id: int
    user_id: int
    started_at: str
    work_minutes: int = 25
    break_minutes: int = 5
    subject_id: Optional[int] = None
    task_id: Optional[int] = None
    ended_at: Optional[str] = None
    completed: bool = False
    interruptions: int = 0
    notes: str = ""


@dataclass
class FlashcardDeck:
    id: int
    user_id: int
    name: str
    subject_id: Optional[int] = None
    description: str = ""
    color: str = "#7C4DFF"
    card_count: int = 0
    created_at: str = ""
    updated_at: str = ""


@dataclass
class Flashcard:
    id: int
    deck_id: int
    question: str
    answer: str
    q_type: str = "identification"
    choices: str = "[]"
    tags: str = "[]"
    difficulty: int = 1
    sort_order: int = 0
    created_at: str = ""


@dataclass
class FlashcardStudySession:
    id: int
    user_id: int
    deck_id: int
    started_at: str
    ended_at: Optional[str] = None
    total_cards: int = 0
    correct: int = 0
    incorrect: int = 0
    accuracy: float = 0.0


@dataclass
class FlashcardResult:
    id: int
    session_id: int
    flashcard_id: int
    is_correct: bool
    answered_at: str = ""


@dataclass
class Badge:
    id: int
    slug: str
    name: str
    description: str = ""
    icon: str = "trophy"
    category: str = "general"
    xp_reward: int = 50
    is_hidden: bool = False
    # Populated at query time when joined with user_badges
    unlocked_at: Optional[str] = None
    is_unlocked: bool = False


@dataclass
class Skill:
    id: int
    slug: str
    name: str
    description: str = ""
    icon: str = "star"
    max_level: int = 10
    xp_per_level: int = 100
    # Populated at query time when joined with user_skills
    current_level: int = 0
    current_xp: int = 0
    total_xp: int = 0


@dataclass
class StreakEntry:
    id: int
    user_id: int
    date: str
    streak_type: str = "daily"


@dataclass
class AccountabilityEntry:
    id: int
    user_id: int
    date: str
    score: float = 0.0
    breakdown_json: str = "{}"
    created_at: str = ""


@dataclass
class Setting:
    id: int
    user_id: int
    key: str
    value: str = ""
    updated_at: str = ""


@dataclass
class Notification:
    id: int
    user_id: int
    notif_type: str
    title: str
    body: str
    scheduled_at: str
    ref_id: Optional[int] = None
    is_sent: bool = False
    created_at: str = ""
