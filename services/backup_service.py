"""Backup and export service."""
from __future__ import annotations
import csv
import json
import shutil
from datetime import datetime
from pathlib import Path
from utils.logger import get_logger
from config import DATABASE_PATH, BACKUPS_DIR, EXPORTS_DIR, BACKUP_MAX_COUNT

log = get_logger(__name__)


# ── DB Backup / Restore ────────────────────────────────────────────────────

def create_backup() -> Path:
    """Copy the SQLite DB file to the backups directory."""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    dest = BACKUPS_DIR / f"tasklyn_backup_{ts}.db"
    shutil.copy2(str(DATABASE_PATH), str(dest))
    log.info("Backup created: %s", dest)
    _prune_old_backups()
    return dest


def list_backups() -> list[Path]:
    return sorted(BACKUPS_DIR.glob("tasklyn_backup_*.db"), reverse=True)


def restore_backup(backup_path: str | Path) -> tuple[bool, str]:
    backup_path = Path(backup_path)
    if not backup_path.exists():
        return False, "Backup file not found."
    try:
        shutil.copy2(str(backup_path), str(DATABASE_PATH))
        log.info("Restored from: %s", backup_path)
        return True, "Database restored. Please restart the app."
    except Exception as exc:
        log.error("Restore failed: %s", exc)
        return False, str(exc)


def _prune_old_backups() -> None:
    backups = list_backups()
    for old in backups[BACKUP_MAX_COUNT:]:
        old.unlink(missing_ok=True)


# ── CSV Export ─────────────────────────────────────────────────────────────

def export_tasks_csv(user_id: int) -> Path:
    from database.repositories import TaskRepository, SubjectRepository
    tasks = TaskRepository().get_for_user(user_id)
    subjs = {s.id: s.name for s in SubjectRepository().get_for_user(user_id)}
    path = EXPORTS_DIR / f"tasks_{datetime.now().strftime('%Y%m%d')}.csv"
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["ID", "Title", "Subject", "Priority", "Status",
                    "Deadline", "Created", "Completed"])
        for t in tasks:
            w.writerow([t.id, t.title, subjs.get(t.subject_id or 0, ""),
                        t.priority, t.status, t.deadline or "",
                        t.created_at[:10], t.completed_at[:10] if t.completed_at else ""])
    log.info("Tasks exported to CSV: %s", path)
    return path


def export_stats_json(user_id: int) -> Path:
    from services.statistics_service import get_monthly_stats
    stats = get_monthly_stats(user_id)
    path = EXPORTS_DIR / f"stats_{datetime.now().strftime('%Y%m%d')}.json"
    path.write_text(json.dumps(stats, indent=2), encoding="utf-8")
    log.info("Stats exported to JSON: %s", path)
    return path


def export_stats_pdf(user_id: int) -> tuple[bool, str, Path | None]:
    """Generate a PDF statistics report using ReportLab."""
    try:
        from reportlab.lib.pagesizes import A4
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
        from reportlab.lib.styles import getSampleStyleSheet
        from reportlab.lib.units import mm
        from services.statistics_service import get_monthly_stats
        from services.gamification_service import get_badge_count, get_skills
        from services.streak_service import get_streak_summary

        stats = get_monthly_stats(user_id)
        streak = get_streak_summary(user_id)
        badges = get_badge_count(user_id)

        path = EXPORTS_DIR / f"report_{datetime.now().strftime('%Y%m%d_%H%M')}.pdf"
        doc = SimpleDocTemplate(str(path), pagesize=A4,
                                leftMargin=20*mm, rightMargin=20*mm,
                                topMargin=20*mm, bottomMargin=20*mm)
        styles = getSampleStyleSheet()
        story = [
            Paragraph("Tasklyn — Monthly Report", styles["Title"]),
            Spacer(1, 5*mm),
            Paragraph(f"Period: {stats['start']} to {stats['end']}", styles["Normal"]),
            Spacer(1, 3*mm),
            Paragraph(f"Tasks Completed: {stats['tasks_completed']}", styles["Normal"]),
            Paragraph(f"Tasks Late: {stats['tasks_late']}", styles["Normal"]),
            Paragraph(f"Study Hours: {stats['study_minutes']//60}h {stats['study_minutes']%60}m", styles["Normal"]),
            Paragraph(f"Pomodoro Sessions: {stats['pomodoro_sessions']}", styles["Normal"]),
            Paragraph(f"Flashcard Accuracy: {stats['flashcard_accuracy']}%", styles["Normal"]),
            Spacer(1, 5*mm),
            Paragraph(f"Current Streak: {streak['current']} days", styles["Normal"]),
            Paragraph(f"Longest Streak: {streak['longest']} days", styles["Normal"]),
            Paragraph(f"Badges Earned: {badges}", styles["Normal"]),
        ]
        doc.build(story)
        log.info("PDF report generated: %s", path)
        return True, "Report saved.", path
    except ImportError:
        return False, "ReportLab not installed. Run: pip install reportlab", None
    except Exception as exc:
        log.error("PDF export failed: %s", exc)
        return False, str(exc), None
