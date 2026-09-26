"""
Tasklyn — Auth / Profile Service
====================================
Handles first-launch detection, profile creation, and profile updates.
"""
from __future__ import annotations
from typing import Optional
from database.repositories import UserRepository, SettingsRepository
from models import User
from utils.logger import get_logger
from utils.validation import validate_name

log = get_logger(__name__)
_user_repo = UserRepository()
_settings_repo = SettingsRepository()

# Cached active user in-process
_active_user: Optional[User] = None


def is_first_launch() -> bool:
    """Return True if no user profile exists yet."""
    return _user_repo.get_first() is None


def get_active_user() -> Optional[User]:
    """Return the active (first) user; None if not set up yet."""
    global _active_user
    if _active_user is None:
        _active_user = _user_repo.get_first()
    return _active_user


def create_profile(name: str, avatar_id: str, gender: str, password: Optional[str] = None) -> tuple[bool, str, Optional[User]]:
    """
    Create the user profile.

    Returns
    -------
    (success, error_message, user)
    """
    global _active_user
    ok, err = validate_name(name, "Name")
    if not ok:
        return False, err, None
    try:
        user = _user_repo.create(name=name.strip(), avatar_id=avatar_id, gender=gender, password=password)
        _active_user = user
        log.info("Profile created: %s (id=%d)", user.name, user.id)
        return True, "", user
    except Exception as exc:
        log.error("Failed to create profile: %s", exc, exc_info=True)
        return False, "Failed to save profile. Please try again.", None


def update_profile(name: str, avatar_id: str, gender: str) -> tuple[bool, str]:
    user = get_active_user()
    if not user:
        return False, "No profile found."
    ok, err = validate_name(name, "Name")
    if not ok:
        return False, err
    try:
        _user_repo.update_profile(user.id, name.strip(), avatar_id, gender)
        user.name = name.strip()
        user.avatar_id = avatar_id
        user.gender = gender
        log.info("Profile updated: %s", user.name)
        return True, ""
    except Exception as exc:
        log.error("Failed to update profile: %s", exc, exc_info=True)
        return False, "Failed to update profile."


def refresh_active_user() -> Optional[User]:
    global _active_user
    _active_user = _user_repo.get_first()
    return _active_user


def authenticate(name: str, password: str) -> tuple[bool, str, Optional[User]]:
    """Authenticate a user by name and password."""
    global _active_user
    user = _user_repo.get_first()
    if not user:
        return False, "No profile exists yet.", None
    
    if user.name.lower() != name.lower().strip():
        return False, "User not found.", None
    
    if user.password != password:
        return False, "Incorrect password.", None
    
    _active_user = user
    return True, "", user
