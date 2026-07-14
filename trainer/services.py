from collections import Counter
from datetime import date, timedelta

from django.db.models import Avg, Count, Sum
from django.utils import timezone
from django.utils.text import slugify

from .data import LESSONS, MOCK_USAGE_EVENTS
from .models import (
    Achievement,
    ApplicationUsage,
    Lesson,
    PracticeSession,
    Progress,
    Quiz,
    QuizResult,
    Recommendation,
    Shortcut,
    UsageEvent,
    UserAchievement,
)


ACHIEVEMENT_DEFINITIONS = [
    ("first-lesson", "First Lesson", "Complete your first guided lesson.", 100, 1),
    ("first-perfect-quiz", "First Perfect Quiz", "Score 100% accuracy in a quiz.", 150, 1),
    ("seven-day-streak", "7 Day Streak", "Practice for seven active days.", 250, 7),
    ("thirty-day-streak", "30 Day Streak", "Build a month-long keyboard habit.", 750, 30),
    ("one-hundred-shortcuts", "100 Shortcuts Learned", "Complete 100 shortcut drills.", 500, 100),
    ("keyboard-ninja", "Keyboard Ninja", "Reach level 10 with strong accuracy.", 400, 10),
    ("productivity-explorer", "Productivity Explorer", "Connect anonymous desktop productivity signals.", 200, 1),
]


EXTRA_SHORTCUTS = [
    ("Chrome", "Switch Tabs", "Ctrl+Tab", "control,tab", "Move to the next browser tab.", "Use during research or dashboards.", "Jump between docs and reports.", "Browser", "Intermediate", "Chrome,Edge,Firefox", 18),
    ("Chrome", "Previous Tab", "Ctrl+Shift+Tab", "control,shift,tab", "Move to the previous browser tab.", "Use when comparing adjacent tabs.", "Return to a source article.", "Browser", "Intermediate", "Chrome,Edge,Firefox", 18),
    ("Chrome", "Hard Refresh", "Ctrl+Shift+R", "control,shift,r", "Reload without cached assets.", "Use while checking updated pages.", "Refresh a changed dashboard.", "Browser", "Advanced", "Chrome,Edge,Firefox", 20),
    ("Edge", "Open Favorites", "Ctrl+Shift+O", "control,shift,o", "Open bookmark manager.", "Use to organize saved pages.", "Clean up research bookmarks.", "Browser", "Intermediate", "Edge,Chrome", 16),
    ("Firefox", "Private Window", "Ctrl+Shift+P", "control,shift,p", "Open a private browser window.", "Use for isolated sessions.", "Check a page without stored state.", "Browser", "Intermediate", "Firefox", 14),
    ("Windows", "Screenshot Snip", "Win+Shift+S", "meta,shift,s", "Capture a screen region.", "Use when sharing visual context.", "Snip a chart into a ticket.", "Capture", "Beginner", "Windows", 30),
    ("Windows", "Open Settings", "Win+I", "meta,i", "Open Windows Settings.", "Use when changing system preferences.", "Open display settings quickly.", "System", "Beginner", "Windows", 12),
    ("VS Code", "Find File", "Ctrl+P", "control,p", "Open files by name.", "Use when navigating projects.", "Jump to views.py instantly.", "Code", "Intermediate", "VS Code", 38),
    ("VS Code", "Format Document", "Shift+Alt+F", "shift,alt,f", "Format the current document.", "Use before committing code.", "Clean a JSON file.", "Code", "Intermediate", "VS Code", 28),
    ("VS Code", "Rename Symbol", "F2", "f2", "Rename a symbol project-wide.", "Use during refactors.", "Rename a variable safely.", "Code", "Advanced", "VS Code", 55),
    ("Word", "Italic Text", "Ctrl+I", "control,i", "Italicize selected text.", "Use for emphasis or titles.", "Format a report title.", "Formatting", "Beginner", "Word,Google Docs", 10),
    ("Word", "Underline Text", "Ctrl+U", "control,u", "Underline selected text.", "Use in structured documents.", "Mark a required field.", "Formatting", "Beginner", "Word,Google Docs", 10),
    ("Excel", "Insert Row", "Ctrl+Shift+Plus", "control,shift,+", "Insert selected rows or columns.", "Use while cleaning sheets.", "Add a row for a missing region.", "Spreadsheet", "Intermediate", "Excel,Google Sheets", 25),
    ("Excel", "Edit Cell", "F2", "f2", "Edit the active cell.", "Use without double-clicking.", "Fix a formula quickly.", "Spreadsheet", "Beginner", "Excel,Google Sheets", 18),
    ("PowerPoint", "Duplicate Slide", "Ctrl+D", "control,d", "Duplicate selected slide or object.", "Use while building decks.", "Create a similar agenda slide.", "Presentation", "Beginner", "PowerPoint", 22),
    ("PowerPoint", "New Slide", "Ctrl+M", "control,m", "Insert a new slide.", "Use while outlining a deck.", "Add a section divider.", "Presentation", "Beginner", "PowerPoint", 18),
    ("Google Docs", "Insert Link", "Ctrl+K", "control,k", "Add a link to selected text.", "Use while documenting sources.", "Link to a spec from notes.", "Editing", "Beginner", "Google Docs,Google Sheets,Chrome", 20),
    ("Google Sheets", "Fill Down", "Ctrl+D", "control,d", "Fill selected cells downward.", "Use with repeated formulas.", "Copy a formula through a column.", "Spreadsheet", "Intermediate", "Google Sheets,Excel", 30),
    ("Figma", "Group Selection", "Ctrl+G", "control,g", "Group selected layers.", "Use while organizing designs.", "Group button elements.", "Design", "Beginner", "Figma", 20),
    ("Figma", "Frame Selection", "Ctrl+Alt+G", "control,alt,g", "Frame selected layers.", "Use to structure layouts.", "Frame a component variant.", "Design", "Advanced", "Figma", 35),
    ("Photoshop", "Free Transform", "Ctrl+T", "control,t", "Transform selected layer.", "Use when resizing artwork.", "Scale a product cutout.", "Design", "Intermediate", "Photoshop", 32),
    ("Photoshop", "Merge Layers", "Ctrl+E", "control,e", "Merge selected layers.", "Use when flattening edits.", "Merge retouching layers.", "Design", "Advanced", "Photoshop", 24),
    ("General", "Print", "Ctrl+P", "control,p", "Open print or export dialog.", "Use when creating PDFs.", "Export a signed report.", "File", "Beginner", "Windows,Chrome,Word,Excel", 16),
]


def ensure_catalog_seeded():
    previous_lesson = None
    for lesson_data in LESSONS:
        lesson, _ = Lesson.objects.update_or_create(
            slug=slugify(lesson_data["title"]),
            defaults={
                "title": lesson_data["title"],
                "level": lesson_data.get("level", lesson_data["difficulty"]).lower().replace("-specific", ""),
                "category": lesson_data["category"],
                "difficulty": lesson_data["difficulty"],
                "order": lesson_data["id"],
                "estimated_minutes": lesson_data["duration"],
                "unlock_after": previous_lesson,
            },
        )
        Quiz.objects.get_or_create(lesson=lesson, defaults={"title": f"{lesson.title} Quiz"})
        for order, shortcut in enumerate(lesson_data["shortcuts"], start=1):
            Shortcut.objects.update_or_create(
                lesson=lesson,
                name=shortcut["name"],
                defaults={
                    "windows_combo": "+".join(shortcut["combo"]),
                    "mac_combo": "+".join(shortcut.get("mac_combo", [])),
                    "key_signature": ",".join(shortcut["keys"]),
                    "purpose": shortcut["purpose"],
                    "when_to_use": shortcut["when"],
                    "example": shortcut["example"],
                    "category": shortcut["category"],
                    "difficulty": shortcut["difficulty"],
                    "apps": ",".join(shortcut["apps"]),
                    "estimated_seconds_saved": shortcut["saved"],
                    "order": order,
                },
            )
        previous_lesson = lesson

    library_lesson, _ = Lesson.objects.get_or_create(
        slug="complete-shortcut-library",
        defaults={
            "title": "Complete Shortcut Library",
            "level": "application",
            "category": "Reference",
            "difficulty": "Mixed",
            "order": 99,
            "estimated_minutes": 15,
            "unlock_after": previous_lesson,
        },
    )
    Quiz.objects.get_or_create(lesson=library_lesson, defaults={"title": "Complete Shortcut Library Quiz"})
    for order, item in enumerate(EXTRA_SHORTCUTS, start=1):
        app, name, combo, signature, purpose, when, example, category, difficulty, apps, saved = item
        Shortcut.objects.update_or_create(
            lesson=library_lesson,
            name=f"{app}: {name}",
            defaults={
                "windows_combo": combo,
                "key_signature": signature,
                "purpose": purpose,
                "when_to_use": when,
                "example": example,
                "category": category,
                "difficulty": difficulty,
                "apps": apps,
                "estimated_seconds_saved": saved,
                "order": order,
            },
        )

    for badge_key, name, description, xp_reward, _target in ACHIEVEMENT_DEFINITIONS:
        Achievement.objects.update_or_create(
            badge_key=badge_key,
            defaults={"name": name, "description": description, "xp_reward": xp_reward},
        )


def get_progress(user):
    ensure_catalog_seeded()
    first_lesson = Lesson.objects.order_by("order").first()
    if not user.is_authenticated:
        return Progress(current_lesson=first_lesson, xp=0, level=1, streak_days=0, estimated_time_saved_minutes=0)
    progress, _ = Progress.objects.get_or_create(
        user=user,
        defaults={"current_lesson": first_lesson},
    )
    if not progress.current_lesson and first_lesson:
        progress.current_lesson = first_lesson
        progress.save(update_fields=["current_lesson", "updated_at"])
    return progress


def lessons_for_trainer():
    ensure_catalog_seeded()
    lessons = []
    for lesson in Lesson.objects.prefetch_related("shortcuts").exclude(slug="complete-shortcut-library"):
        shortcuts = []
        for shortcut in lesson.shortcuts.all():
            shortcuts.append({
                "id": shortcut.id,
                "name": shortcut.name,
                "combo": shortcut.windows_combo.split("+"),
                "mac_combo": shortcut.mac_combo.split("+") if shortcut.mac_combo else [],
                "keys": [key.strip().lower() for key in shortcut.key_signature.split(",")],
                "task": shortcut.purpose,
                "purpose": shortcut.purpose,
                "when": shortcut.when_to_use,
                "example": shortcut.example,
                "saved": shortcut.estimated_seconds_saved,
                "apps": [app.strip() for app in shortcut.apps.split(",") if app.strip()],
                "category": shortcut.category,
                "difficulty": shortcut.difficulty,
            })
        lessons.append({
            "id": lesson.order,
            "db_id": lesson.id,
            "title": lesson.title,
            "category": lesson.category,
            "difficulty": lesson.difficulty,
            "duration": lesson.estimated_minutes,
            "shortcuts": shortcuts,
        })
    return lessons


def all_library_shortcuts():
    ensure_catalog_seeded()
    shortcuts = []
    for shortcut in Shortcut.objects.select_related("lesson").all():
        shortcuts.append({
            "name": shortcut.name,
            "combo": shortcut.windows_combo.split("+"),
            "purpose": shortcut.purpose,
            "when": shortcut.when_to_use,
            "example": shortcut.example,
            "saved": shortcut.estimated_seconds_saved,
            "apps": [app.strip() for app in shortcut.apps.split(",") if app.strip()],
            "category": shortcut.category,
            "difficulty": shortcut.difficulty,
            "lesson_title": shortcut.lesson.title,
        })
    return shortcuts


def seed_simulated_usage(user):
    if UsageEvent.objects.filter(user=user).exists():
        return
    for item in MOCK_USAGE_EVENTS:
        UsageEvent.objects.create(user=user, **item)
    today = date.today()
    ApplicationUsage.objects.update_or_create(
        user=user,
        app_name="Chrome",
        observed_on=today,
        defaults={"window_class": "Chrome_WidgetWin", "active_seconds": 9840, "switch_count": 38},
    )
    ApplicationUsage.objects.update_or_create(
        user=user,
        app_name="Excel",
        observed_on=today,
        defaults={"window_class": "XLMAIN", "active_seconds": 5520, "switch_count": 17},
    )


def usage_summary(user):
    if user.is_authenticated:
        seed_simulated_usage(user)
        events = UsageEvent.objects.filter(user=user)
        apps_qs = ApplicationUsage.objects.filter(user=user)
    else:
        events = UsageEvent.objects.none()
        apps_qs = ApplicationUsage.objects.none()
    counts = Counter()
    for event in events:
        counts[event.event_key] += event.count
        counts[event.event_type] += event.count
    total_active = apps_qs.aggregate(total=Sum("active_seconds"))["total"] or 0
    app_switches = counts["app_switch"] or apps_qs.aggregate(total=Sum("switch_count"))["total"] or 0
    mouse_clicks = counts["mouse_click"]
    clipboard = counts["clipboard_action"] or counts["copy"]
    keyboard = counts["keyboard_shortcut"]
    new_tabs = counts["new_tab"]
    closed_tabs = counts["close_tab"]
    manual_saves = counts["manual_save"]
    idle_minutes = round((counts["idle"] or 0) / 60)
    potential = round((clipboard * 2 + app_switches * 1 + manual_saves * 3 + closed_tabs * 4) / 60)
    apps = [
        {
            "name": app.app_name,
            "minutes": round(app.active_seconds / 60),
            "switches": app.switch_count,
            "score": min(100, 48 + round(app.active_seconds / 240)),
        }
        for app in apps_qs.order_by("-active_seconds")[:5]
    ]
    # Generate dynamic, personalized coach insights from telemetry counts
    insights = []
    tab_switches = counts.get("ctrl_tab", 0) + counts.get("ctrl_shift_tab", 0)
    if tab_switches > 0:
        insights.append(f"You switched browser tabs {tab_switches} times today using shortcuts.")
    elif new_tabs > 5:
        insights.append(f"You opened {new_tabs} browser tabs but did not use Ctrl+Tab to cycle through them.")

    copies = counts.get("copy", 0)
    if copies > 0:
        insights.append(f"You manually copied text {copies} times.")
    elif clipboard > 5:
        insights.append(f"You performed {clipboard} clipboard actions today.")

    scrolls = counts.get("mouse_scroll", 0)
    double_clicks = counts.get("double_click", 0)
    if mouse_clicks > 50:
        insights.append(f"You performed {mouse_clicks} mouse clicks (including {double_clicks} double-clicks and {scrolls} scrolls) indicating high pointer usage.")

    if keyboard > 0:
        insights.append(f"You utilized keyboard shortcuts {keyboard} times to optimize your workflow.")
    else:
        insights.append("You rarely use keyboard shortcuts in active applications. Start with basic navigation combos.")

    if app_switches > 20:
        insights.append(f"You switched application windows {app_switches} times today. Alt+Tab can keep your hands on the keyboard.")

    if not insights:
        insights = [
            "Start the desktop agent to collect local workflow events and generate insights.",
            "Complete guided drills to build shortcut muscle memory."
        ]

    return {
        "productivity_score": min(100, 62 + min(24, keyboard // 8) + min(8, total_active // 7200)),
        "potential_time_saved_minutes": potential,
        "focus_time_minutes": round(total_active / 60),
        "idle_minutes": idle_minutes,
        "app_switches": app_switches,
        "mouse_clicks": mouse_clicks,
        "keyboard_shortcuts": keyboard,
        "clipboard_actions": clipboard,
        "browser_tabs_opened": new_tabs,
        "browser_tabs_closed": closed_tabs,
        "manual_saves": manual_saves,
        "repeated_workflows": counts["workflow_repeat"],
        "most_used_apps": apps,
        "coach_insights": insights,
        "time_wasters": [
            {"label": "Browser tab churn", "detail": f"{new_tabs} new tabs and {closed_tabs} tab closes.", "minutes": max(1, round((new_tabs + closed_tabs) / 8))},
            {"label": "Repeated copy and paste", "detail": f"{clipboard} clipboard actions across work apps.", "minutes": max(1, round(clipboard / 18))},
            {"label": "Frequent app switching", "detail": f"{app_switches} switches between core work apps.", "minutes": max(1, round(app_switches / 14))},
            {"label": "Manual save loop", "detail": f"{manual_saves} save-related actions in document tools.", "minutes": max(1, round(manual_saves / 15))},
        ],
        "weak_areas": (
            list(dict.fromkeys([
                item for s in PracticeSession.objects.filter(user=user).exclude(weak_areas=[])
                if isinstance(s.weak_areas, list) for item in s.weak_areas
            ]))[:4]
            if user.is_authenticated else []
        ) or ["No weak areas recorded yet. Keep practicing!"],
        "strengths": (
            [f"Mastered: {lesson.title}" for lesson in Lesson.objects.filter(id__in=get_progress(user).completed_lessons)]
            if user.is_authenticated else []
        ) or [
            "Practice data is stored in SQLite.",
            "Coach recommendations come from usage events.",
            "Privacy-first agent only sends anonymous counts.",
        ],
        "recent_activity": [
            f"Stored {events.count()} anonymous productivity signal rows.",
            f"Tracked {apps_qs.count()} application usage summaries.",
            "Generated recommendations from SQLite usage events.",
        ],
    }


def recommendations_for(user):
    summary = usage_summary(user)
    definitions = [
        (summary["clipboard_actions"], "Paste Without Formatting", "Ctrl+Shift+V", f"You copied or pasted text {summary['clipboard_actions']} times. Learn Ctrl+Shift+V for clean paste workflows.", 86),
        (summary["app_switches"], "Switch Applications", "Alt+Tab", f"You switched apps {summary['app_switches']} times. Learn Alt+Tab to reduce pointer travel.", 84),
        (summary["manual_saves"], "Save", "Ctrl+S", f"You manually saved {summary['manual_saves']} times. Learn Ctrl+S to keep the save habit fast.", 79),
        (summary["browser_tabs_closed"], "Reopen Closed Tab", "Ctrl+Shift+T", f"You closed tabs {summary['browser_tabs_closed']} times. Learn Ctrl+Shift+T for fast recovery.", 88),
        (summary["browser_tabs_opened"], "Switch Tabs", "Ctrl+Tab", f"You opened {summary['browser_tabs_opened']} tabs. Learn Ctrl+Tab to move through research faster.", 82),
    ]
    recs = []
    for count, title, combo, reason, confidence in sorted(definitions, reverse=True):
        if count <= 0:
            continue
        shortcut = Shortcut.objects.filter(name__icontains=title.split()[0]).first()
        if user.is_authenticated:
            Recommendation.objects.update_or_create(
                user=user,
                title=title,
                defaults={
                    "shortcut": shortcut,
                    "reason": reason,
                    "estimated_seconds_saved_daily": count * 2,
                    "confidence": confidence,
                    "source_signal": f"{count} events",
                },
            )
        recs.append({"signal": f"{count} events", "shortcut": title, "combo": combo, "reason": reason, "daily_saved": max(1, round(count / 18)), "confidence": confidence})
    return recs[:5]


def user_stats(user):
    ensure_catalog_seeded()
    progress = get_progress(user)
    total_shortcuts = Shortcut.objects.count()
    total_lessons = Lesson.objects.exclude(slug="complete-shortcut-library").count()
    sessions = PracticeSession.objects.filter(user=user) if user.is_authenticated else PracticeSession.objects.none()
    quizzes = QuizResult.objects.filter(user=user) if user.is_authenticated else QuizResult.objects.none()
    completed_lessons = len(progress.completed_lessons or [])
    completed_shortcuts = len(progress.completed_shortcuts or [])
    avg_accuracy = sessions.aggregate(avg=Avg("accuracy"))["avg"] or quizzes.aggregate(avg=Avg("accuracy"))["avg"] or 0
    today = timezone.localdate()
    weekly = []
    for days_back in range(6, -1, -1):
        day = today - timedelta(days=days_back)
        day_sessions = sessions.filter(started_at__date=day)
        weekly.append(int(day_sessions.aggregate(total=Sum("completed_shortcuts"))["total"] or 0) * 3)
    max_weekly = max(weekly) if weekly and max(weekly) > 0 else 1
    weekly_scaled = [round((val / max_weekly) * 100) for val in weekly]
    return {
        "total_shortcuts": total_shortcuts,
        "total_lessons": total_lessons,
        "completed_shortcuts": completed_shortcuts,
        "completed_lessons": completed_lessons,
        "weekly_minutes": weekly,
        "weekly_scaled": weekly_scaled,
        "xp": progress.xp,
        "level": progress.level,
        "streak": progress.streak_days,
        "time_saved_minutes": progress.estimated_time_saved_minutes,
        "accuracy": round(float(avg_accuracy)),
        "course_progress": round((completed_shortcuts / total_shortcuts) * 100) if total_shortcuts else 0,
        "today_progress": min(100, sessions.filter(started_at__date=today).count() * 25),
        "time_spent_minutes": sum(weekly),
        "quiz_count": quizzes.count(),
    }


def unlock_achievements(user):
    stats = user_stats(user)
    usage = usage_summary(user)
    perfect_quiz = QuizResult.objects.filter(user=user, accuracy=100).exists()
    unlocked_rows = []
    for badge_key, _name, _description, _xp, target in ACHIEVEMENT_DEFINITIONS:
        achievement = Achievement.objects.get(badge_key=badge_key)
        value = {
            "first-lesson": stats["completed_lessons"],
            "first-perfect-quiz": 1 if perfect_quiz else 0,
            "seven-day-streak": stats["streak"],
            "thirty-day-streak": stats["streak"],
            "one-hundred-shortcuts": stats["completed_shortcuts"],
            "keyboard-ninja": stats["level"],
            "productivity-explorer": 1 if usage["app_switches"] or usage["clipboard_actions"] else 0,
        }[badge_key]
        row, _ = UserAchievement.objects.get_or_create(user=user, achievement=achievement, defaults={"target": target})
        row.target = target
        row.progress = min(value, target)
        if value >= target and not row.unlocked_at:
            row.unlocked_at = timezone.now()
        row.save()
        unlocked_rows.append(row)
    return unlocked_rows


def record_practice_result(user, payload):
    ensure_catalog_seeded()
    lesson = Lesson.objects.filter(id=payload.get("lesson_db_id")).first() or Lesson.objects.filter(order=payload.get("lesson_order")).first()
    session = PracticeSession.objects.create(
        user=user if user.is_authenticated else None,
        lesson=lesson,
        completed_at=timezone.now(),
        completed_shortcuts=int(payload.get("completed_shortcuts", 0)),
        total_shortcuts=int(payload.get("total_shortcuts", 0)),
        accuracy=float(payload.get("accuracy", 0)),
        average_speed_seconds=float(payload.get("average_speed_seconds", 0)),
        xp_earned=int(payload.get("xp_earned", 0)),
        weak_areas=payload.get("weak_areas", []),
    )
    if user.is_authenticated:
        progress = get_progress(user)
        completed_lessons = set(progress.completed_lessons or [])
        completed_shortcuts = set(progress.completed_shortcuts or [])
        if lesson:
            completed_lessons.add(lesson.id)
            for shortcut in lesson.shortcuts.all():
                completed_shortcuts.add(shortcut.id)
        progress.completed_lessons = sorted(completed_lessons)
        progress.completed_shortcuts = sorted(completed_shortcuts)
        progress.xp += session.xp_earned
        progress.level = max(1, progress.xp // 500 + 1)
        progress.streak_days = max(progress.streak_days, 1)
        progress.estimated_time_saved_minutes += round(sum(s.estimated_seconds_saved for s in lesson.shortcuts.all()) / 60) if lesson else 0
        next_lesson = Lesson.objects.exclude(id__in=progress.completed_lessons).exclude(slug="complete-shortcut-library").order_by("order").first()
        progress.current_lesson = next_lesson or lesson
        progress.save()
        unlock_achievements(user)
    return session


def record_quiz_result(user, payload):
    lesson = Lesson.objects.filter(id=payload.get("lesson_db_id")).first() or Lesson.objects.filter(order=payload.get("lesson_order")).first()
    quiz = Quiz.objects.filter(lesson=lesson).first() if lesson else None
    result = QuizResult.objects.create(
        user=user if user.is_authenticated else None,
        quiz=quiz,
        score=int(payload.get("score", 0)),
        accuracy=float(payload.get("accuracy", 0)),
        reaction_time_seconds=float(payload.get("reaction_time_seconds", 0)),
        wrong_attempts=int(payload.get("wrong_attempts", 0)),
    )
    if user.is_authenticated:
        unlock_achievements(user)
    return result


def get_heatmap_data(user):
    if not user.is_authenticated:
        return [{"level": 0, "count": 0, "day_name": (date.today() - timedelta(days=i)).strftime("%A"), "date_str": (date.today() - timedelta(days=i)).strftime("%b %d")} for i in range(27, -1, -1)]

    today = date.today()
    heatmap_data = []
    for days_back in range(27, -1, -1):
        day = today - timedelta(days=days_back)
        sessions_count = PracticeSession.objects.filter(user=user, started_at__date=day).count()
        quizzes_count = QuizResult.objects.filter(user=user, completed_at__date=day).count()
        total_count = sessions_count + quizzes_count
        
        if total_count == 0:
            level = 0
        elif total_count <= 2:
            level = 1
        elif total_count <= 5:
            level = 2
        else:
            level = 3
            
        heatmap_data.append({
            "level": level,
            "count": total_count,
            "day_name": day.strftime("%A"),
            "date_str": day.strftime("%b %d"),
        })
    return heatmap_data


def get_progress_trends(user):
    if not user.is_authenticated:
        return {"accuracies": [0] * 8, "xps": [0] * 8}
    
    sessions = PracticeSession.objects.filter(user=user).order_by("-started_at")[:8]
    sessions = list(reversed(sessions))
    
    accuracies = [int(s.accuracy) for s in sessions]
    xps = [s.xp_earned for s in sessions]
    
    while len(accuracies) < 8:
        accuracies.insert(0, 0)
    while len(xps) < 8:
        xps.insert(0, 0)
        
    return {
        "accuracies": accuracies,
        "xps": xps,
    }


def get_completed_lessons_details(user):
    if not user.is_authenticated:
        return []
    progress = get_progress(user)
    completed_ids = progress.completed_lessons or []
    return list(Lesson.objects.filter(id__in=completed_ids).values("id", "title", "category", "difficulty"))
