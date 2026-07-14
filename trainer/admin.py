from django.contrib import admin

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


admin.site.register(Achievement)
admin.site.register(ApplicationUsage)
admin.site.register(Lesson)
admin.site.register(PracticeSession)
admin.site.register(Progress)
admin.site.register(Quiz)
admin.site.register(QuizResult)
admin.site.register(Recommendation)
admin.site.register(Shortcut)
admin.site.register(UsageEvent)
admin.site.register(UserAchievement)
