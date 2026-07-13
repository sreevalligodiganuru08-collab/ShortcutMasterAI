from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.http import JsonResponse
from datetime import date, timedelta
from .models import User, Achievement, UserAchievement
from shortcuts.models import Shortcut, Application
from practice.models import PracticeSession
from shortcuts.recommendations import get_recommendations
from analytics.models import ActivityLog

# Custom Creation Form to support AbstractUser properties
class PremiumUserCreationForm(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = User
        fields = UserCreationForm.Meta.fields + ('email', 'preferred_os')

def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    # Count stats for landing marketing card
    total_users = User.objects.count()
    total_shortcuts = Shortcut.objects.count()
    return render(request, 'landing.html', {
        'total_users': total_users or 120,
        'total_shortcuts': total_shortcuts or 240
    })

def signup_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = PremiumUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            ActivityLog.objects.create(user=user, activity_type='login', details='New account registration.')
            messages.success(request, f"Welcome to ShortcutMaster AI, {user.username}!")
            return redirect('dashboard')
        else:
            messages.error(request, "Failed to create account. Please check the details.")
    else:
        form = PremiumUserCreationForm()
    return render(request, 'auth/signup.html', {'form': form})

def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        form = AuthenticationForm(request, data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get('username')
            password = form.cleaned_data.get('password')
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                ActivityLog.objects.create(user=user, activity_type='login', details='Standard login.')
                messages.success(request, f"Welcome back, {username}!")
                return redirect('dashboard')
        messages.error(request, "Invalid username or password.")
    else:
        form = AuthenticationForm()
    return render(request, 'auth/login.html', {'form': form})

def logout_view(request):
    if request.user.is_authenticated:
        logout(request)
        messages.success(request, "Logged out successfully.")
    return redirect('landing')

@login_required
def dashboard(request):
    user = request.user
    
    # Log dashboard view
    ActivityLog.objects.create(user=user, activity_type='view_dashboard')
    
    # Calculate stats
    sessions = PracticeSession.objects.filter(user=user)
    correct_sessions = sessions.filter(is_correct=True)
    
    total_practices = sessions.count()
    correct_practices = correct_sessions.count()
    accuracy = round((correct_practices / total_practices * 100), 1) if total_practices > 0 else 0.0
    
    # Time saved: sum up savings for each successful practice
    time_saved_sec = correct_sessions.aggregate(total=Sum('shortcut__estimated_time_saved'))['total'] or 0.0
    time_saved_min = round(float(time_saved_sec) / 60.0, 1)

    # Weekly practices data for Chart.js
    today = date.today()
    start_of_week = today - timedelta(days=today.weekday())
    daily_stats = []
    days_of_week = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']
    
    for i in range(7):
        target_day = start_of_week + timedelta(days=i)
        cnt = sessions.filter(created_at__date=target_day).count()
        daily_stats.append(cnt)

    # AI Recommended Shortcuts
    recommendations = get_recommendations(user, limit=3)
    
    # Unlocked Achievements
    unlocked = UserAchievement.objects.filter(user=user).select_related('achievement')
    recent_achievements = [ua.achievement for ua in unlocked[:3]]
    
    # Recent log items
    recent_logs = sessions.order_by('-created_at')[:5]
    
    context = {
        'total_practices': total_practices,
        'accuracy': accuracy,
        'streak': user.streak,
        'xp': user.xp,
        'level': user.level,
        'time_saved_min': time_saved_min,
        'daily_stats': daily_stats,
        'days_of_week': days_of_week,
        'recommendations': recommendations,
        'recent_achievements': recent_achievements,
        'recent_logs': recent_logs,
        'xp_to_next': user.level * 200,
        'xp_percent': min(int((user.xp / (user.level * 200)) * 100), 100) if user.level > 0 else 0
    }
    return render(request, 'dashboard.html', context)

def leaderboard(request):
    users = User.objects.order_by('-xp')[:10]
    return render(request, 'leaderboard.html', {'leaderboard_users': users})

@login_required
def settings_view(request):
    user = request.user
    if request.method == 'POST':
        email = request.POST.get('email')
        preferred_os = request.POST.get('preferred_os')
        bio = request.POST.get('bio')
        avatar = request.POST.get('avatar')
        
        user.email = email
        user.preferred_os = preferred_os
        user.bio = bio
        if avatar:
            user.avatar = avatar
        user.save()
        messages.success(request, "Settings updated successfully!")
        return redirect('settings')
        
    avatars = [f"avatar-{i}.svg" for i in range(1, 9)]
    return render(request, 'settings.html', {
        'avatars': avatars,
        'os_choices': ['windows', 'mac']
    })

def about(request):
    return render(request, 'about.html')

def contact(request):
    if request.method == 'POST':
        messages.success(request, "Message sent successfully! Our AI team will get back to you shortly.")
        return redirect('contact')
    return render(request, 'contact.html')

def custom_404(request, exception):
    return render(request, '404.html', status=404)
