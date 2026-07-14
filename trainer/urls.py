from django.urls import path

from . import views

urlpatterns = [
    path("", views.index, name="index"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("practice/", views.practice, name="practice"),
    path("coach/", views.coach, name="coach"),
    path("library/", views.library, name="library"),
    path("achievements/", views.achievements, name="achievements"),
    path("progress/", views.progress, name="progress"),
    path("reports/", views.reports, name="reports"),
    path("profile/", views.profile, name="profile"),
    path("api/practice/result/", views.save_practice_result, name="save_practice_result"),
    path("api/quiz/result/", views.save_quiz_result, name="save_quiz_result"),
    path("api/agent/usage/", views.ingest_usage_summary, name="ingest_usage_summary"),
    path("login/", views.ShortcutLoginView.as_view(), name="login"),
    path("logout/", views.ShortcutLogoutView.as_view(), name="logout"),
    path("register/", views.register, name="register"),
    path("forgot-password/", views.forgot_password, name="forgot_password"),
]
