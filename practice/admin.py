from django.contrib import admin
from .models import PracticeSession

class PracticeSessionAdmin(admin.ModelAdmin):
    list_display = ('user', 'shortcut', 'accuracy', 'response_time', 'is_correct', 'xp_earned', 'created_at')
    list_filter = ('is_correct', 'created_at')
    search_fields = ('user__username', 'shortcut__description')

admin.site.register(PracticeSession, PracticeSessionAdmin)
