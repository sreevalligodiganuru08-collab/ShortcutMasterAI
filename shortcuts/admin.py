from django.contrib import admin
from .models import Application, Shortcut

class ShortcutAdmin(admin.ModelAdmin):
    list_display = ('description', 'application', 'keys_windows', 'keys_mac', 'category', 'difficulty', 'estimated_time_saved')
    list_filter = ('application', 'category', 'difficulty')
    search_fields = ('description', 'keys_windows', 'keys_mac')

admin.site.register(Application)
admin.site.register(Shortcut, ShortcutAdmin)
