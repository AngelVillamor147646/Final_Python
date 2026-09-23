"""
Tasklyn — Database Integration Tests
"""
import os, sys, tempfile, pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

@pytest.fixture(autouse=True)
def tmp_db(monkeypatch, tmp_path):
    """Redirect DB to a temp file for each test."""
    import config as cfg
    db_path = tmp_path / "test.db"
    monkeypatch.setattr(cfg, "DATABASE_PATH", db_path)
    monkeypatch.setattr(cfg, "USER_DATA_DIR", tmp_path)
    from database.connection import init_database, _local
    _local.__dict__.clear()
    init_database()
    yield
    from database.connection import close_connection
    close_connection()


def test_create_user():
    from database.repositories import UserRepository
    repo = UserRepository()
    user = repo.create("Alice", "girl_smile", "girl")
    assert user.id is not None
    assert user.name == "Alice"
    assert user.gender == "girl"


def test_first_launch_detection():
    from services.auth_service import is_first_launch
    assert is_first_launch() is True


def test_create_profile():
    from services.auth_service import create_profile, is_first_launch
    ok, err, user = create_profile("Bob", "boy_neutral", "boy")
    assert ok is True
    assert err == ""
    assert user is not None
    assert is_first_launch() is False


def test_create_and_get_task():
    from services.auth_service import create_profile
    _, _, user = create_profile("Test", "boy_neutral", "boy")
    from services.task_service import create_task, get_task
    ok, err, task = create_task(user.id, "Study math", priority="high")
    assert ok
    fetched = get_task(task.id)
    assert fetched.title == "Study math"
    assert fetched.priority == "high"


def test_complete_task():
    from services.auth_service import create_profile
    _, _, user = create_profile("Test2", "boy_neutral", "boy")
    from services.task_service import create_task, complete_task, get_task
    _, _, task = create_task(user.id, "Finish homework")
    ok, badges = complete_task(task.id, user.id)
    assert ok
    updated = get_task(task.id)
    assert updated.status == "done"


def test_streak_recording():
    from services.auth_service import create_profile
    _, _, user = create_profile("Test3", "boy_neutral", "boy")
    from services.streak_service import record_activity, get_current_streak
    record_activity(user.id)
    assert get_current_streak(user.id) == 1
    record_activity(user.id)  # idempotent
    assert get_current_streak(user.id) == 1


def test_settings_get_set():
    from services.auth_service import create_profile
    _, _, user = create_profile("Test4", "boy_neutral", "boy")
    from database.repositories import SettingsRepository
    s = SettingsRepository()
    s.set(user.id, "theme", "Light")
    assert s.get(user.id, "theme") == "Light"


def test_subject_creation():
    from services.auth_service import create_profile
    _, _, user = create_profile("Test5", "boy_neutral", "boy")
    from database.repositories import SubjectRepository
    repo = SubjectRepository()
    subj = repo.create(user.id, "Mathematics", "#FF5733")
    assert subj.name == "Mathematics"
    assert subj.user_id == user.id


def test_schedule_creation():
    from services.auth_service import create_profile
    _, _, user = create_profile("Test6", "boy_neutral", "boy")
    from services.schedule_service import create_schedule, get_day_schedule
    ok, err, sc = create_schedule(user.id, "Calculus", 0, "08:00", "09:30")
    assert ok
    classes = get_day_schedule(user.id, 0)
    assert any(c.title == "Calculus" for c in classes)


def test_conflict_detection():
    from services.auth_service import create_profile
    _, _, user = create_profile("Test7", "boy_neutral", "boy")
    from services.schedule_service import create_schedule
    create_schedule(user.id, "Math", 1, "09:00", "10:00")
    ok, err, _ = create_schedule(user.id, "Science", 1, "09:30", "10:30")
    assert not ok
    assert "conflict" in err.lower()


def test_pomodoro_session():
    from services.auth_service import create_profile
    _, _, user = create_profile("Test8", "boy_neutral", "boy")
    from services.pomodoro_service import start_session, complete_session
    session = start_session(user.id, work_min=1, break_min=1)
    assert session.id is not None
    badges = complete_session(session.id, user.id)
    assert isinstance(badges, list)
