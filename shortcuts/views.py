from django.shortcuts import render
from .models import Application, Shortcut
from django.db.models import Q
from analytics.models import ActivityLog

# Note: Django's get_object_or_404 is standard, let's use it correctly.
from django.shortcuts import get_object_or_404

def library(request, app_slug=None):
    apps = Application.objects.all()
    active_app = None
    shortcuts = Shortcut.objects.all()
    
    if app_slug:
        active_app = get_object_or_404(Application, slug=app_slug)
        shortcuts = shortcuts.filter(application=active_app)
    elif apps.exists():
        active_app = apps.first()
        shortcuts = shortcuts.filter(application=active_app)
        
    # Search functionality
    query = request.GET.get('q')
    if query:
        shortcuts = shortcuts.filter(
            Q(description__icontains=query) |
            Q(keys_windows__icontains=query) |
            Q(keys_mac__icontains=query) |
            Q(category__icontains=query)
        )
        
    # OS Preference
    os_pref = request.GET.get('os')
    if not os_pref:
        if request.user.is_authenticated:
            os_pref = request.user.preferred_os
        else:
            os_pref = 'windows'
            
    # Activity log
    if request.user.is_authenticated:
        ActivityLog.objects.create(
            user=request.user, 
            activity_type='view_shortcut', 
            details=f"Viewed {active_app.name if active_app else 'All'} library (OS: {os_pref})"
        )

    return render(request, 'shortcuts/library.html', {
        'apps': apps,
        'active_app': active_app,
        'shortcuts': shortcuts,
        'os_pref': os_pref,
        'query': query,
    })
