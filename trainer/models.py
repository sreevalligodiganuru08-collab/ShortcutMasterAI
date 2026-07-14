from django.conf import settings
from django.db import models
import json


class JSONTextField(models.TextField):
    description = "JSON value stored as text"

    def __init__(self, *args, default=None, **kwargs):
        if default is None:
            default = dict
        self.json_default = default
        super().__init__(*args, default=default, **kwargs)

    def from_db_value(self, value, expression, connection):
        return self.to_python(value)

    def to_python(self, value):
        if value is None:
            return self._default_value()
        if isinstance(value, (dict, list)):
            return value
        if value == "":
            return self._default_value()
        try:
            return json.loads(value)
        except (TypeError, ValueError):
            return self._default_value()

    def get_prep_value(self, value):
        if value is None:
            value = self._default_value()
        return json.dumps(value)

    def _default_value(self):
        return self.json_default() if callable(self.json_default) else self.json_default

    def deconstruct(self):
        name, path, args, kwargs = super().deconstruct()
        path = "trainer.models.JSONTextField"
        kwargs["default"] = self.json_default
        return name, path, args, kwargs


class Lesson(models.Model):
    LEVEL_CHOICES = [
        ("beginner", "Beginner"),
        ("intermediate", "Intermediate"),
        ("advanced", "Advanced"),
        ("application", "Application-specific"),
    ]

    title = models.CharField(max_length=160)
    slug = models.SlugField(unique=True)
    level = models.CharField(max_length=24, choices=LEVEL_CHOICES)
    app_focus = models.CharField(max_length=80, blank=True)
    category = models.CharField(max_length=80)
    difficulty = models.CharField(max_length=40)
    order = models.PositiveIntegerField(default=1)
    estimated_minutes = models.PositiveIntegerField(default=5)
    unlock_after = models.ForeignKey("self", null=True, blank=True, on_delete=models.SET_NULL)

    class Meta:
        ordering = ["order", "id"]

    def __str__(self):
        return self.title


class Shortcut(models.Model):
    lesson = models.ForeignKey(Lesson, related_name="shortcuts", on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    windows_combo = models.CharField(max_length=120)
    mac_combo = models.CharField(max_length=120, blank=True)
    key_signature = models.CharField(max_length=180)
    purpose = models.TextField()
    when_to_use = models.TextField()
    example = models.TextField()
    category = models.CharField(max_length=80)
    difficulty = models.CharField(max_length=40)
    apps = models.CharField(max_length=240)
    estimated_seconds_saved = models.PositiveIntegerField(default=10)
    order = models.PositiveIntegerField(default=1)

    class Meta:
        ordering = ["lesson__order", "order", "id"]

    def __str__(self):
        return f"{self.name} ({self.windows_combo})"


class PracticeSession(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    lesson = models.ForeignKey(Lesson, null=True, blank=True, on_delete=models.SET_NULL)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    completed_shortcuts = models.PositiveIntegerField(default=0)
    total_shortcuts = models.PositiveIntegerField(default=0)
    accuracy = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    average_speed_seconds = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    xp_earned = models.PositiveIntegerField(default=0)
    weak_areas = JSONTextField(default=list, blank=True)


class Quiz(models.Model):
    lesson = models.ForeignKey(Lesson, related_name="quizzes", on_delete=models.CASCADE)
    title = models.CharField(max_length=160)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class QuizResult(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    quiz = models.ForeignKey(Quiz, null=True, blank=True, on_delete=models.SET_NULL)
    score = models.PositiveIntegerField(default=0)
    accuracy = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    reaction_time_seconds = models.DecimalField(max_digits=6, decimal_places=2, default=0)
    wrong_attempts = models.PositiveIntegerField(default=0)
    completed_at = models.DateTimeField(auto_now_add=True)


class ApplicationUsage(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    app_name = models.CharField(max_length=120)
    window_class = models.CharField(max_length=160, blank=True)
    active_seconds = models.PositiveIntegerField(default=0)
    switch_count = models.PositiveIntegerField(default=0)
    observed_on = models.DateField()

    class Meta:
        unique_together = ("user", "app_name", "observed_on")


class UsageEvent(models.Model):
    EVENT_CHOICES = [
        ("mouse_click", "Mouse click"),
        ("keyboard_shortcut", "Keyboard shortcut"),
        ("app_switch", "Application switch"),
        ("clipboard_action", "Clipboard action"),
        ("browser_action", "Browser action"),
        ("idle", "Idle"),
        ("workflow_repeat", "Repeated workflow"),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    event_type = models.CharField(max_length=40, choices=EVENT_CHOICES)
    app_name = models.CharField(max_length=120, blank=True)
    event_key = models.CharField(max_length=120)
    count = models.PositiveIntegerField(default=1)
    metadata = JSONTextField(default=dict, blank=True)
    occurred_at = models.DateTimeField(auto_now_add=True)


class Recommendation(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL)
    shortcut = models.ForeignKey(Shortcut, null=True, blank=True, on_delete=models.SET_NULL)
    title = models.CharField(max_length=180)
    reason = models.TextField()
    estimated_seconds_saved_daily = models.PositiveIntegerField(default=0)
    confidence = models.PositiveIntegerField(default=75)
    source_signal = models.CharField(max_length=120, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)


class Achievement(models.Model):
    name = models.CharField(max_length=120)
    description = models.TextField()
    xp_reward = models.PositiveIntegerField(default=0)
    badge_key = models.SlugField(unique=True)

    def __str__(self):
        return self.name


class UserAchievement(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    progress = models.PositiveIntegerField(default=0)
    target = models.PositiveIntegerField(default=1)
    unlocked_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ("user", "achievement")


class Progress(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    current_lesson = models.ForeignKey(Lesson, null=True, blank=True, on_delete=models.SET_NULL)
    completed_lessons = JSONTextField(default=list, blank=True)
    completed_shortcuts = JSONTextField(default=list, blank=True)
    xp = models.PositiveIntegerField(default=0)
    level = models.PositiveIntegerField(default=1)
    streak_days = models.PositiveIntegerField(default=0)
    estimated_time_saved_minutes = models.PositiveIntegerField(default=0)
    updated_at = models.DateTimeField(auto_now=True)
