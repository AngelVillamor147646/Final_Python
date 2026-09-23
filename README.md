# Tasklyn — Academic Management System

> A fully offline, cross-platform academic management system built with Python, Kivy, KivyMD, and SQLite.

---

## Features

| Module | Description |
|---|---|
| **Dashboard** | KPI cards, today's tasks, classes, Pomodoro summary, streak, badges |
| **Task Manager** | Full CRUD, priorities, labels, deadlines, reminders, recurring tasks |
| **Schedule** | Weekly timetable with conflict detection, daily view, class reminders |
| **Pomodoro Timer** | Animated ring timer, work/break cycles, session logging, notifications |
| **Flashcards** | Markdown import, MCQ + identification, mistake repetition, accuracy tracking |
| **Skills** | 5 skills with XP system, levels, and progress bars |
| **Badges** | 25 achievement badges with automatic unlock engine |
| **Streaks** | Daily/weekly streaks with calendar heatmap |
| **Accountability** | 5-factor score engine with daily history and trend chart |
| **Statistics** | Bar/line/pie charts for study hours, tasks, accuracy, subjects |
| **Reflection** | Weekly summary with rule-based improvement suggestions |
| **Settings** | Theme, backup/restore, export (CSV/PDF), profile editing |

---

## Tech Stack

- **Python** 3.11+
- **Kivy** 2.3 + **KivyMD** 1.2
- **SQLite** 3 (stdlib `sqlite3`)
- **Plyer** (notifications)
- **Matplotlib** (embedded charts)
- **ReportLab** (PDF export)

---

## Installation

### Prerequisites

```bash
pip install kivy==2.3.0 kivymd==1.2.0 plyer matplotlib reportlab
```

### Run

```bash
cd tasklyn
python main.py
```

### Run Tests

```bash
cd tasklyn
pytest tests/ -v
```

---

## Project Structure

```
tasklyn/
├── main.py              # App entry point
├── config.py            # All constants and paths
├── requirements.txt
├── buildozer.spec       # Android packaging
├── assets/              # Fonts, icons, avatars
├── database/            # SQLite connection, schema, migrations, repositories
├── models/              # Dataclasses for all entities
├── services/            # Business logic layer
├── views/               # Kivy screens and widgets
├── themes/              # Dark/light theme tokens
├── flashcards/          # Markdown parser and validator
├── statistics/          # Matplotlib chart builder
├── animations/          # Kivy animation helpers
├── utils/               # Logger, date utils, helpers, validation
└── tests/               # pytest test suite
```

---

## Flashcard Markdown Format

```markdown
# Deck: My Deck
subject: Mathematics
color: #42A5F5

## Q: What is 2+2?
A: 4

## Q: Which is prime?
type: multiple_choice
- 4
- 6
* 7
- 9
A: 7
```

**Rules:** 20–100 cards per deck. Use `## Q:` for questions, `A:` for answers.  
For MCQ: `- wrong` and `* correct`.

---

## Android Build

```bash
# Install buildozer (Linux/WSL required)
pip install buildozer
cd tasklyn
buildozer android debug
```

---

## Data Location

All user data (database, backups, exports, logs) is stored in `~/.tasklyn/`.

---

## License

MIT License — see [LICENSE](LICENSE) for details.
