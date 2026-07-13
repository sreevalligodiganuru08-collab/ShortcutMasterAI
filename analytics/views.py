from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Sum, Count, Avg
from datetime import date, timedelta
from practice.models import PracticeSession
from shortcuts.models import Shortcut

@login_required
def analytics_home(request):
    user = request.user
    sessions = PracticeSession.objects.filter(user=user)
    correct_sessions = sessions.filter(is_correct=True)
    
    # General metrics
    total_count = sessions.count()
    correct_count = correct_sessions.count()
    accuracy = round((correct_count / total_count * 100), 1) if total_count > 0 else 0.0
    
    total_time_saved_sec = correct_sessions.aggregate(total=Sum('shortcut__estimated_time_saved'))['total'] or 0.0
    total_time_saved_min = round(float(total_time_saved_sec) / 60.0, 1)
    
    avg_speed = round(sessions.aggregate(avg_time=Avg('response_time'))['avg_time'] or 0.0, 2)
    
    context = {
        'total_count': total_count,
        'correct_count': correct_count,
        'accuracy': accuracy,
        'total_time_saved_min': total_time_saved_min,
        'avg_speed': avg_speed,
        'streak': user.streak,
        'level': user.level
    }
    return render(request, 'analytics/home.html', context)

@login_required
def analytics_data(request):
    user = request.user
    sessions = PracticeSession.objects.filter(user=user)
    
    # 1. Weekly timeline data (Last 7 days)
    today = date.today()
    timeline_labels = []
    timeline_values = []
    for i in range(6, -1, -1):
        target_day = today - timedelta(days=i)
        cnt = sessions.filter(created_at__date=target_day).count()
        timeline_labels.append(target_day.strftime('%b %d'))
        timeline_values.append(cnt)
        
    # 2. Accuracy rate by Category
    categories = ['navigation', 'editing', 'window', 'terminal', 'system', 'formatting', 'search']
    category_labels = [cat.title() for cat in categories]
    category_accs = []
    
    for cat in categories:
        cat_sessions = sessions.filter(shortcut__category=cat)
        if cat_sessions.exists():
            correct_cat = cat_sessions.filter(is_correct=True).count()
            acc = round((correct_cat / cat_sessions.count() * 100), 1)
        else:
            acc = 0.0
        category_accs.append(acc)
        
    # 3. Practice distribution by Difficulty
    difficulties = ['easy', 'medium', 'hard']
    diff_labels = ['Easy', 'Medium', 'Hard']
    diff_counts = []
    for diff in difficulties:
        diff_counts.append(sessions.filter(shortcut__difficulty=diff).count())
        
    return JsonResponse({
        'timeline_labels': timeline_labels,
        'timeline_values': timeline_values,
        'category_labels': category_labels,
        'category_accs': category_accs,
        'diff_labels': diff_labels,
        'diff_counts': diff_counts
    })
