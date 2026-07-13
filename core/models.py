from django.contrib.auth.models import AbstractUser
from django.db import models

class User(AbstractUser):
    xp = models.IntegerField(default=0)
    level = models.IntegerField(default=1)
    streak = models.IntegerField(default=0)
    last_active = models.DateField(null=True, blank=True)
    avatar = models.CharField(max_length=100, default='avatar-1.svg', help_text='Avatar name') # We can use static SVG avatars for instant clean premium loading
    preferred_os = models.CharField(
        max_length=10, 
        choices=[('windows', 'Windows'), ('mac', 'macOS')], 
        default='windows'
    )
    bio = models.TextField(max_length=500, blank=True, default='')

    def __str__(self):
        return self.username

class Achievement(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField()
    badge_icon = models.CharField(max_length=50, default='award', help_text='Icon glyph name or character')
    xp_reward = models.IntegerField(default=100)

    def __str__(self):
        return self.name

class UserAchievement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='achievements')
    achievement = models.ForeignKey(Achievement, on_delete=models.CASCADE)
    unlocked_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('user', 'achievement')

    def __str__(self):
        return f"{self.user.username} unlocked {self.achievement.name}"
