"""Accountability and streak tests."""
import os, sys, pytest
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

@pytest.fixture(autouse=True)
def tmp_db(monkeypatch, tmp_path):
    import config as cfg
    monkeypatch.setattr(cfg, "DATABASE_PATH", tmp_path / "test.db")
    monkeypatch.setattr(cfg, "USER_DATA_DIR", tmp_path)
    from database.connection import _local, init_database
    _local.__dict__.clear()
    init_database()
    yield
    from database.connection import close_connection; close_connection()


def _make_user(name="User"):
    from services.auth_service import create_profile
    _, _, user = create_profile(name, "boy_neutral", "boy")
    return user


def test_accountability_score_zero_activity():
    user = _make_user("Acc1")
    from services.gamification_service import calculate_accountability_score
    result = calculate_accountability_score(user.id)
    assert 0 <= result["total"] <= 100


def test_accountability_improves_with_task():
    user = _make_user("Acc2")
    from services.task_service import create_task, complete_task
    from services.gamification_service import calculate_accountability_score
    create_task(user.id, "Task A", priority="medium")
    score_before = calculate_accountability_score(user.id)["total"]
    _, _, task = create_task(user.id, "Task B", priority="high")
    complete_task(task.id, user.id)
    score_after = calculate_accountability_score(user.id)["total"]
    assert score_after >= score_before


def test_streak_increments():
    from datetime import date, timedelta
    user = _make_user("Str1")
    from database.repositories import StreakRepository
    repo = StreakRepository()
    today = date.today()
    yesterday = today - timedelta(days=1)
    repo._execute("INSERT OR IGNORE INTO streaks (user_id, date, streak_type) VALUES (?,?,?)",
                  (user.id, yesterday.isoformat(), "daily"))
    repo._commit()
    repo.record_today(user.id)
    assert repo.current_streak(user.id) == 2


def test_longest_streak():
    from datetime import date, timedelta
    user = _make_user("Str2")
    from database.repositories import StreakRepository
    repo = StreakRepository()
    base = date.today()
    for i in range(5):
        d = (base - timedelta(days=10-i)).isoformat()
        repo._execute("INSERT OR IGNORE INTO streaks (user_id, date, streak_type) VALUES (?,?,?)",
                      (user.id, d, "daily"))
    repo._commit()
    assert repo.longest_streak(user.id) == 5


def test_badge_unlock():
    user = _make_user("Badge1")
    from database.repositories import BadgeRepository
    repo = BadgeRepository()
    assert not repo.is_unlocked(user.id, "first_task")
    badge = repo.unlock(user.id, "first_task")
    assert badge is not None
    assert repo.is_unlocked(user.id, "first_task")
    # Double unlock returns None
    assert repo.unlock(user.id, "first_task") is None


def test_skill_xp_levelup():
    user = _make_user("Skill1")
    from database.repositories import SkillRepository
    repo = SkillRepository()
    # XP per level for time_management is 120
    result = repo.add_xp(user.id, "time_management", 120)
    assert result["leveled_up"] is True
    assert result["new_level"] == 1


def test_skill_no_levelup():
    user = _make_user("Skill2")
    from database.repositories import SkillRepository
    repo = SkillRepository()
    result = repo.add_xp(user.id, "focus", 50)
    assert result["leveled_up"] is False
    assert result["new_xp"] == 50
