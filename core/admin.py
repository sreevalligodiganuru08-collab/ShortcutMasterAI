from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User, Achievement, UserAchievement

class CustomUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (
        ('Gamification & Preferences', {'fields': ('xp', 'level', 'streak', 'preferred_os', 'avatar', 'bio')}),
    )
    list_display = ('username', 'email', 'level', 'xp', 'streak', 'preferred_os', 'is_staff')
    list_filter = ('preferred_os', 'is_staff', 'is_superuser')

admin.site.register(User, CustomUserAdmin)
admin.site.register(Achievement)
admin.site.register(UserAchievement)
