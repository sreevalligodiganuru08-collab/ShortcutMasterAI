import json
from datetime import date

from django.contrib.auth import get_user_model
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from .models import ApplicationUsage, PracticeSession, Progress, QuizResult, UsageEvent
from .services import ensure_catalog_seeded


@override_settings(SECURE_SSL_REDIRECT=False)
class ShortcutMasterSmokeTests(TestCase):
    def setUp(self):
        ensure_catalog_seeded()
        self.user = get_user_model().objects.create_user(
            username="qa-user",
            password="strong-test-password",
        )
        self.client = Client()

    def test_public_pages_render(self):
        for name in ["index", "library", "login", "register", "forgot_password"]:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)

    def test_authenticated_pages_render(self):
        self.client.force_login(self.user)
        for name in [
            "dashboard",
            "practice",
            "coach",
            "achievements",
            "progress",
            "reports",
            "profile",
        ]:
            response = self.client.get(reverse(name))
            self.assertEqual(response.status_code, 200, name)

    def test_practice_and_quiz_results_persist(self):
        self.client.force_login(self.user)
        practice_payload = {
            "lesson_order": 1,
            "completed_shortcuts": 2,
            "total_shortcuts": 2,
            "accuracy": 100,
            "average_speed_seconds": 1.2,
            "xp_earned": 120,
            "weak_areas": [],
        }
        practice_response = self.client.post(
            reverse("save_practice_result"),
            data=json.dumps(practice_payload),
            content_type="application/json",
        )
        self.assertEqual(practice_response.status_code, 200)
        self.assertEqual(PracticeSession.objects.filter(user=self.user).count(), 1)
        self.assertTrue(Progress.objects.filter(user=self.user, xp__gte=120).exists())

        quiz_response = self.client.post(
            reverse("save_quiz_result"),
            data=json.dumps({"lesson_order": 1, "score": 2, "accuracy": 100, "reaction_time_seconds": 1.4}),
            content_type="application/json",
        )
        self.assertEqual(quiz_response.status_code, 200)
        self.assertEqual(QuizResult.objects.filter(user=self.user).count(), 1)

    def test_local_agent_telemetry_ingestion_persists_sqlite_rows(self):
        payload = {
            "applications": [
                {
                    "app_name": "Chrome",
                    "window_class": "Chrome_WidgetWin",
                    "active_seconds": 120,
                    "switch_count": 4,
                    "observed_on": date.today().isoformat(),
                }
            ],
            "events": [
                {
                    "event_type": "keyboard_shortcut",
                    "event_key": "ctrl_tab",
                    "count": 3,
                    "metadata": {"app_name": "Chrome"},
                }
            ],
        }
        response = self.client.post(
            reverse("ingest_usage_summary"),
            data=json.dumps(payload),
            content_type="application/json",
            REMOTE_ADDR="127.0.0.1",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(UsageEvent.objects.count(), 1)
        self.assertEqual(ApplicationUsage.objects.count(), 1)

    def test_remote_agent_telemetry_rejected(self):
        response = self.client.post(
            reverse("ingest_usage_summary"),
            data=json.dumps({"applications": [], "events": []}),
            content_type="application/json",
            REMOTE_ADDR="10.0.0.2",
        )
        self.assertEqual(response.status_code, 403)
