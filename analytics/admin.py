from django.contrib import admin
from .models import ActivityLog

class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'activity_type', 'shortcut', 'timestamp')
    list_filter = ('activity_type', 'timestamp')
    search_fields = ('user__username', 'details')

admin.site.register(ActivityLog, ActivityLogAdmin)
