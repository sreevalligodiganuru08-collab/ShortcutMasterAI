import json

from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm, PasswordResetForm, UserCreationForm
from django.contrib.auth.views import LoginView, LogoutView
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import redirect, render
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST

from .services import (
    all_library_shortcuts,
    ensure_catalog_seeded,
    lessons_for_trainer,
    recommendations_for,
    record_practice_result,
    record_quiz_result,
    unlock_achievements,
    usage_summary,
    user_stats,
    get_progress,
    get_heatmap_data,
    get_progress_trends,
    get_completed_lessons_details,
)
from .models import ApplicationUsage, PracticeSession, QuizResult, UsageEvent


def index(request):
    ensure_catalog_seeded()
    lessons = lessons_for_trainer()
    context = {"stats": user_stats(request.user), "lessons": lessons[:3], "shortcuts": all_library_shortcuts()[:6]}
    return render(request, "index.html", context)


@login_required
def dashboard(request):
    stats = user_stats(request.user)
    usage = usage_summary(request.user)
    recs = recommendations_for(request.user)
    lessons = lessons_for_trainer()
    progress = get_progress(request.user)
    progress_lesson = next((lesson for lesson in lessons if lesson["db_id"] == progress.current_lesson_id), None)
    current_lesson = progress_lesson or (lessons[0] if lessons else None)
    context = {
        "stats": stats,
        "lessons": lessons,
        "current_lesson": current_lesson,
        "usage": usage,
        "recommendations": recs[:3],
        "recent_activity": usage["recent_activity"],
        "recent_practice": PracticeSession.objects.filter(user=request.user).select_related("lesson").order_by("-started_at")[:4],
        "recent_achievements": unlock_achievements(request.user)[:3],
    }
    return render(request, "dashboard.html", context)


@login_required
def practice(request):
    context = {
        "lessons": lessons_for_trainer(),
        "stats": user_stats(request.user),
    }
    return render(request, "practice.html", context)


@login_required
def coach(request):
    usage = usage_summary(request.user)
    recs = recommendations_for(request.user)
    return render(
        request,
        "coach.html",
        {
            "usage": usage,
            "recommendations": recs,
            "stats": user_stats(request.user),
        },
    )


def library(request):
    shortcuts = all_library_shortcuts()
    apps = sorted({app for shortcut in shortcuts for app in shortcut["apps"]})
    categories = sorted({shortcut["category"] for shortcut in shortcuts})
    difficulties = sorted({shortcut["difficulty"] for shortcut in shortcuts})
    return render(
        request,
        "library.html",
        {
            "shortcuts": shortcuts,
            "apps": apps,
            "categories": categories,
            "difficulties": difficulties,
        },
    )


@login_required
def progress(request):
    stats = user_stats(request.user)
    sessions = PracticeSession.objects.filter(user=request.user).order_by("-started_at")
    quizzes = QuizResult.objects.filter(user=request.user).order_by("-completed_at")
    from .models import UserAchievement
    unlocked_badges = UserAchievement.objects.filter(user=request.user, unlocked_at__isnull=False).count()
    trends = get_progress_trends(request.user)
    completed_lessons_list = get_completed_lessons_details(request.user)
    heatmap = get_heatmap_data(request.user)
    return render(
        request,
        "progress.html",
        {
            "stats": stats,
            "unlocked_badges": unlocked_badges,
            "achievements": unlock_achievements(request.user),
            "sessions": sessions[:8],
            "quizzes": quizzes[:8],
            "heatmap": heatmap,
            "trends": trends,
            "completed_lessons_list": completed_lessons_list,
            "calendar_days": ["M", "T", "W", "T", "F", "S", "S"],
        },
    )


@login_required
def reports(request):
    usage = usage_summary(request.user)
    return render(
        request,
        "reports.html",
        {
            "usage": usage,
            "recommendations": recommendations_for(request.user),
            "stats": user_stats(request.user),
        },
    )


@login_required
def achievements(request):
    return render(request, "achievements.html", {"achievements": unlock_achievements(request.user), "stats": user_stats(request.user)})


@login_required
def profile(request):
    stats = user_stats(request.user)
    sessions = PracticeSession.objects.filter(user=request.user).select_related("lesson").order_by("-started_at")[:6]
    achievements = unlock_achievements(request.user)
    apps = [app["name"] for app in usage_summary(request.user)["most_used_apps"]] or ["Windows", "Chrome", "VS Code"]
    return render(
        request,
        "profile.html",
        {
            "stats": stats,
            "history": sessions,
            "achievements": achievements,
            "preferred_apps": apps,
        },
    )


class ShortcutLoginView(LoginView):
    template_name = "auth/login.html"
    authentication_form = AuthenticationForm

    def form_valid(self, form):
        response = super().form_valid(form)
        if not self.request.POST.get("remember_me"):
            self.request.session.set_expiry(0)
        return response


class ShortcutLogoutView(LogoutView):
    pass


def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            ensure_catalog_seeded()
            user_stats(user)
            usage_summary(user)
            return redirect("dashboard")
    else:
        form = UserCreationForm()
    return render(request, "auth/register.html", {"form": form})


def forgot_password(request):
    form = PasswordResetForm(request.POST or None)
    submitted = request.method == "POST" and form.is_valid()
    return render(request, "auth/forgot_password.html", {"form": form, "submitted": submitted})


@login_required
@require_POST
def save_practice_result(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON payload."}, status=400)
    session = record_practice_result(request.user, payload)
    return JsonResponse({"ok": True, "session_id": session.id, "stats": user_stats(request.user)})


@login_required
@require_POST
def save_quiz_result(request):
    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON payload."}, status=400)
    result = record_quiz_result(request.user, payload)
    return JsonResponse({"ok": True, "quiz_result_id": result.id, "stats": user_stats(request.user)})


def _local_agent_allowed(request):
    forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR", "")
    remote_addr = forwarded_for.split(",")[0].strip() if forwarded_for else request.META.get("REMOTE_ADDR")
    return remote_addr in {"127.0.0.1", "::1", "localhost"}


@csrf_exempt
@require_POST
def ingest_usage_summary(request):
    if not _local_agent_allowed(request):
        return HttpResponseForbidden("Local agent API accepts localhost traffic only.")

    try:
        payload = json.loads(request.body.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        return JsonResponse({"ok": False, "error": "Invalid JSON payload."}, status=400)

    events = payload.get("events", [])
    apps = payload.get("applications", [])
    user = request.user if request.user.is_authenticated else None

    saved_events = 0
    for event in events:
        event_type = event.get("event_type")
        event_key = event.get("event_key")
        if not event_type or not event_key:
            continue
        UsageEvent.objects.create(
            user=user,
            event_type=event_type,
            app_name=event.get("app_name", "")[:120],
            event_key=event_key[:120],
            count=max(1, int(event.get("count", 1))),
            metadata=event.get("metadata", {}),
        )
        saved_events += 1

    saved_apps = 0
    for app in apps:
        app_name = app.get("app_name")
        observed_on = app.get("observed_on")
        if not app_name or not observed_on:
            continue
        ApplicationUsage.objects.update_or_create(
            user=user,
            app_name=app_name[:120],
            observed_on=observed_on,
            defaults={
                "window_class": app.get("window_class", "")[:160],
                "active_seconds": max(0, int(app.get("active_seconds", 0))),
                "switch_count": max(0, int(app.get("switch_count", 0))),
            },
        )
        saved_apps += 1

    return JsonResponse(
        {
            "ok": True,
            "saved_events": saved_events,
            "saved_applications": saved_apps,
            "privacy": "No typed text, passwords, URLs, document titles, or clipboard contents accepted.",
        }
    )
