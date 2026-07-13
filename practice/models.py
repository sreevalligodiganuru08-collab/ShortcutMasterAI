from django.db import models
from django.conf import settings
from shortcuts.models import Shortcut

class PracticeSession(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='practice_sessions'
    )
    shortcut = models.ForeignKey(
        Shortcut, 
        on_delete=models.CASCADE, 
        related_name='sessions'
    )
    accuracy = models.FloatField(default=100.0, help_text="Accuracy percentage")
    response_time = models.FloatField(help_text="Time taken in seconds")
    is_correct = models.BooleanField(default=True)
    xp_earned = models.IntegerField(default=10)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} - {self.shortcut.description} ({self.created_at.strftime('%Y-%m-%d')})"
