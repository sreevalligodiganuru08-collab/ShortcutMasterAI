# ShortcutMaster AI

> **Learn Smarter. Work Faster.**

ShortcutMaster AI is a production-ready SaaS web application designed to help professionals and developers master keyboard shortcuts, improve typing efficiency, and eliminate reliance on the mouse. 

## Features

- **Personalized AI Recommendation Engine**: Recommends shortcuts based on user behavior and weak categories.
- **Interactive Practice Keyboard**: Captures real-time keystrokes and provides visual feedback on a glassmorphic keyboard.
- **Sleek SaaS Dashboard**: Built-in graphs for weekly tracking, streaks, levels, XP, and time saved metrics.
- **Gamified Elements**: User levels, XP, combos, achievements/badges, and global leaderboards.
- **Comprehensive Shortcut Library**: Built-in libraries for Chrome, VS Code, Excel, Figma, Git, Terminal, Word, PowerPoint, Photoshop.
- **Interactive Quizzes & Daily Challenges**: Tests users on shortcuts.
- **Settings & Preferences**: Support for both Windows and macOS layouts.

## Tech Stack

- **Backend**: Python, Django 4.2.x (MySQL-ready structure, SQLite development)
- **Frontend**: Custom HTML5, Vanilla CSS3 (Glassmorphism, Dark Mode, interactive micro-animations), JavaScript
- **Data Visualization**: Chart.js (via CDN)
- **Static Assets Management**: Whitenoise

## Setup & Running

1. **Clone/Open the repository**:
   Ensure you are in the project folder.

2. **Virtual Environment**:
   A virtual environment `venv` is automatically configured.
   To activate it:
   - **Windows PowerShell**: `.\venv\Scripts\Activate.ps1`
   - **Windows Command Prompt**: `.\venv\Scripts\activate.bat`
   - **macOS/Linux**: `source venv/bin/activate`

3. **Install Dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Run Migrations & Seed Database**:
   ```bash
   python manage.py migrate
   python manage.py seed_db
   ```

5. **Start the Development Server**:
   ```bash
   python manage.py runserver
   ```
   Open `http://127.0.0.1:8000/` in your browser.

## Credentials

- **Admin Account**: `admin` / `admin123`
- **Demo User**: `demouser` / `demo123`
