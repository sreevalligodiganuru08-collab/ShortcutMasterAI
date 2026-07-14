# ShortcutMaster AI

ShortcutMaster AI is a production-ready Django application for learning keyboard shortcuts from real desktop productivity signals. It combines a web learning dashboard, practice drills, quizzes, progress tracking, achievements, an AI-style productivity coach, and a Windows desktop telemetry agent that reports privacy-safe aggregate usage counts to SQLite.

## Problem Statement

Most shortcut trainers teach static lists that are disconnected from the way people actually work. Users often lose time to mouse-heavy navigation, browser tab churn, repeated copy/paste loops, and frequent app switching without seeing which habits cost the most time. ShortcutMaster AI closes that gap by turning local workflow telemetry into targeted practice and measurable productivity progress.

## Features

- Django authentication with registration, login, logout, and password reset screens.
- Dashboard with XP, level, streaks, current lesson, recommendations, and recent activity.
- Guided shortcut practice with client-side scoring and persisted practice sessions.
- Quiz workflow with accuracy, score, reaction time, and SQLite persistence.
- AI Coach page that converts usage telemetry into shortcut recommendations.
- Reports, progress heatmap, achievements, profile, and shortcut library pages.
- Privacy-first Windows desktop agent for local telemetry collection.
- Real-time telemetry ingestion API for app usage, mouse activity, browser actions, clipboard actions, and keyboard shortcut counts.
- Responsive UI with dark mode and collected static assets for deployment.

## Architecture

```text
Windows desktop activity
        |
        v
desktop_agent collector and monitor
        |
        v
Privacy-safe aggregate JSON payload
        |
        v
Django telemetry API: /api/agent/usage/
        |
        v
SQLite models: UsageEvent, ApplicationUsage, PracticeSession, QuizResult, Progress, Achievement
        |
        v
Dashboard, Reports, Progress, Achievements, Library, Practice, Quiz, AI Coach
```

The desktop agent never sends typed text, clipboard contents, URLs, passwords, or raw document content. The Django services layer aggregates SQLite data into user-facing stats, recommendations, lessons, progress charts, and achievements.

## Technology Stack

- Python 3.11.9 on Render
- Django 4.2 LTS
- SQLite
- Gunicorn
- WhiteNoise
- Vanilla JavaScript
- CSS custom properties and responsive layouts
- Windows desktop telemetry with `pynput`, `pywin32`, and `psutil`

## Folder Structure

```text
ShortcutMasterAI/
  desktop_agent/          Windows telemetry agent
  shortcutmaster/         Django project settings, URLs, ASGI, WSGI
  static/                 Source CSS and JavaScript
  staticfiles/            collectstatic output for deployment
  templates/              Django templates
  trainer/                Main Django app, models, services, views, URLs, tests
  db.sqlite3              Local SQLite database
  manage.py               Django management entry point
  Procfile                Deployment process command
  requirements.txt        Python dependencies
  .env.example            Environment variable template
```

## Installation

```bash
git clone https://github.com/sreevalligodiganuru08-collab/ShortcutMasterAI.git
cd ShortcutMasterAI
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
python manage.py migrate
```

## Running Django

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in a browser.

## Running Desktop Agent

Start Django first, then run the desktop telemetry agent in a separate terminal:

```bash
python desktop_agent/agent.py
```

For a single telemetry flush:

```bash
python desktop_agent/agent.py --once
```

The default endpoint is `http://127.0.0.1:8000/api/agent/usage/`.

## Environment Variables

Create `.env` from `.env.example` and configure:

```text
SECRET_KEY=replace-this-secret-key
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com
DATABASE_URL=sqlite:///db.sqlite3
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SECURE_HSTS_SECONDS=31536000
```

`DATABASE_URL` is optional and currently supports SQLite URLs. If omitted, Django uses `db.sqlite3` in the project root.

## Deployment Instructions

### Render

This repository includes `runtime.txt`, `Procfile`, and `render.yaml` for Render deployment.

1. Connect the GitHub repository to Render.
2. Use the included Blueprint or configure a Python web service manually.
3. Set `SECRET_KEY`, `DEBUG=False`, and `ALLOWED_HOSTS` for the Render hostname or custom domain.
4. Use this build command:

```bash
pip install -r requirements.txt && python manage.py collectstatic --noinput && python manage.py migrate
```

5. Use this start command:

```bash
gunicorn shortcutmaster.wsgi:application --log-file -
```

WhiteNoise serves compressed static files from `staticfiles/`. Render's `RENDER_EXTERNAL_HOSTNAME` is automatically added to `ALLOWED_HOSTS` and `CSRF_TRUSTED_ORIGINS` by `shortcutmaster/settings.py`.

## Privacy Policy

ShortcutMaster AI is designed for local-first productivity analysis.

- The desktop agent records aggregate counts only.
- Typed characters, passwords, clipboard contents, URLs, and document contents are not stored or transmitted.
- Window metadata is sanitized before use.
- Telemetry ingestion is restricted to localhost requests.
- SQLite data remains local unless the app is intentionally deployed to a hosted environment.

## Screenshots

Placeholder screenshot slots:

- Dashboard overview: `screenshots/dashboard.png`
- Practice trainer: `screenshots/practice.png`
- AI Coach insights: `screenshots/coach.png`
- Progress heatmap: `screenshots/progress.png`
- Reports dashboard: `screenshots/reports.png`

## Future Scope

- macOS and Linux desktop agents.
- Optional cloud sync with PostgreSQL.
- Team productivity dashboards.
- Smarter recommendation ranking from longer historical telemetry.
- Desktop notifications for shortcut opportunities.

## License

MIT License. Add a `LICENSE` file before public distribution if one is not already present.
