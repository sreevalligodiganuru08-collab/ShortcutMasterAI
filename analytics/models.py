from django.db import models
from django.conf import settings
from shortcuts.models import Shortcut

class ActivityLog(models.Model):
    ACTIVITY_CHOICES = [
        ('login', 'Login'),
        ('view_dashboard', 'View Dashboard'),
        ('view_shortcut', 'View Shortcut'),
        ('start_practice', 'Start Practice'),
        ('complete_practice', 'Complete Practice'),
        ('unlock_achievement', 'Unlock Achievement'),
    ]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE, 
        related_name='activity_logs'
    )
    activity_type = models.CharField(max_length=50, choices=ACTIVITY_CHOICES)
    shortcut = models.ForeignKey(Shortcut, on_delete=models.SET_NULL, null=True, blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    details = models.TextField(blank=True, default='')

    def __str__(self):
        return f"{self.user.username} - {self.activity_type} - {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
