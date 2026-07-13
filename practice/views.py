import json
import random
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from datetime import date
from .models import PracticeSession
from shortcuts.models import Shortcut, Application
from core.models import Achievement, UserAchievement, User
from analytics.models import ActivityLog

def practice_home(request):
    apps = Application.objects.all()
    return render(request, 'practice/home.html', {'apps': apps})

@login_required
def practice_session(request):
    shortcut_id = request.GET.get('shortcut_id')
    os_pref = request.GET.get('os') or request.user.preferred_os
    
    if shortcut_id:
        shortcut = get_object_or_404(Shortcut, id=shortcut_id)
    else:
        # Pick a recommended or random shortcut
        from shortcuts.recommendations import get_recommendations
        recs = get_recommendations(request.user, limit=1)
        if recs:
            shortcut = recs[0]
        else:
            shortcuts = Shortcut.objects.all()
            if not shortcuts.exists():
                return redirect('shortcuts:library')
            shortcut = random.choice(shortcuts)
            
    # Log start practice
    ActivityLog.objects.create(
        user=request.user, 
        activity_type='start_practice', 
        shortcut=shortcut,
        details=f"Started practicing {shortcut.description}"
    )

    return render(request, 'practice/session.html', {
        'shortcut': shortcut,
        'os_pref': os_pref
    })

@login_required
def practice_quiz(request):
    # Multiple choice quiz:
    # 5 questions. In each question, we ask the user what keys trigger a description.
    # We load 5 random shortcuts. For each shortcut, we generate 3 wrong options.
    shortcuts = list(Shortcut.objects.all())
    if len(shortcuts) < 4:
        # Create some standard fallback choices if db is empty
        return redirect('shortcuts:library')
        
    quiz_items = random.sample(shortcuts, min(5, len(shortcuts)))
    os_pref = request.user.preferred_os
    
    questions = []
    for item in quiz_items:
        correct_keys = item.keys_mac if os_pref == 'mac' else item.keys_windows
        
        # Select 3 distractors
        other_items = [s for s in shortcuts if s.id != item.id]
        distractors = random.sample(other_items, min(3, len(other_items)))
        options = [correct_keys]
        for d in distractors:
            d_keys = d.keys_mac if os_pref == 'mac' else d.keys_windows
            if d_keys not in options:
                options.append(d_keys)
        
        # Pad with random strings if we don't have enough options
        while len(options) < 4:
            options.append("Ctrl + Alt + K")
            
        random.shuffle(options)
        
        questions.append({
            'id': item.id,
            'description': item.description,
            'application': item.application.name,
            'correct_option': correct_keys,
            'options': options
        })
        
    return render(request, 'practice/quiz.html', {
        'questions_json': json.dumps(questions),
        'questions': questions
    })

@login_required
def daily_challenge(request):
    # A set of 3 shortcuts that change every day
    # Seed random generator with today's integer to keep it daily-consistent
    today_int = date.today().toordinal()
    random.seed(today_int)
    
    shortcuts = list(Shortcut.objects.all())
    if len(shortcuts) < 3:
        return redirect('shortcuts:library')
        
    daily_items = random.sample(shortcuts, 3)
    
    # Restore random state seed
    random.seed()

    return render(request, 'practice/daily_challenge.html', {
        'shortcuts': daily_items,
        'os_pref': request.user.preferred_os
    })

@csrf_exempt
@login_required
def log_practice(request):
    if request.method != 'POST':
        return HttpResponseBadRequest("Only POST method allowed.")
        
    try:
        data = json.loads(request.body)
        shortcut_id = data.get('shortcut_id')
        accuracy = float(data.get('accuracy', 100))
        response_time = float(data.get('response_time', 1.0))
        is_correct = bool(data.get('is_correct', True))
        is_challenge = bool(data.get('is_challenge', False))
    except (ValueError, TypeError, json.JSONDecodeError):
        return JsonResponse({'status': 'error', 'message': 'Invalid payload parameters'}, status=400)
        
    shortcut = get_object_or_404(Shortcut, id=shortcut_id)
    user = request.user
    
    # XP calculation: Easy=10, Medium=20, Hard=30
    xp_base = 10
    if shortcut.difficulty == 'medium':
        xp_base = 20
    elif shortcut.difficulty == 'hard':
        xp_base = 30
        
    # Accuracy and response time multiplier
    acc_multiplier = accuracy / 100.0
    xp_earned = int(xp_base * acc_multiplier)
    
    if not is_correct:
        xp_earned = 2  # Small participation reward for trying
        
    if is_challenge and is_correct:
        xp_earned *= 2  # Double XP for daily challenges
        
    # Save practice session
    session = PracticeSession.objects.create(
        user=user,
        shortcut=shortcut,
        accuracy=accuracy,
        response_time=response_time,
        is_correct=is_correct,
        xp_earned=xp_earned
    )
    
    # Log Activity
    ActivityLog.objects.create(
        user=user,
        activity_type='complete_practice',
        shortcut=shortcut,
        details=f"Completed practice. Correct: {is_correct}. Accuracy: {accuracy}%. XP: {xp_earned}"
    )
    
    # Update user XP, Level, and Streak
    user.xp += xp_earned
    
    # Check level up (each level requires Level * 200 XP)
    leveled_up = False
    xp_threshold = user.level * 200
    if user.xp >= xp_threshold:
        user.xp -= xp_threshold
        user.level += 1
        leveled_up = True
        
    # Streak check: If last active was yesterday, increment streak. If today, keep. If older, reset to 1.
    today_date = date.today()
    if user.last_active == today_date - date.resolution:  # Yesterday
        user.streak += 1
    elif user.last_active != today_date:  # Not today (either none or older)
        user.streak = 1
    user.last_active = today_date
    user.save()
    
    # Achievements logic
    unlocked_achievements = []
    
    # Check 1: First practice achievement
    first_badge, _ = Achievement.objects.get_or_create(
        slug='first-step',
        defaults={'name': 'First Step', 'description': 'Completed your first practice session.', 'badge_icon': 'bolt', 'xp_reward': 50}
    )
    if not UserAchievement.objects.filter(user=user, achievement=first_badge).exists():
        UserAchievement.objects.create(user=user, achievement=first_badge)
        user.xp += first_badge.xp_reward
        unlocked_achievements.append(first_badge.name)
        
    # Check 2: Accuracy master (100% accuracy)
    if is_correct and accuracy == 100.0:
        acc_badge, _ = Achievement.objects.get_or_create(
            slug='perfectionist',
            defaults={'name': 'Perfectionist', 'description': 'Completed a practice session with 100% accuracy.', 'badge_icon': 'target', 'xp_reward': 100}
        )
        if not UserAchievement.objects.filter(user=user, achievement=acc_badge).exists():
            UserAchievement.objects.create(user=user, achievement=acc_badge)
            user.xp += acc_badge.xp_reward
            unlocked_achievements.append(acc_badge.name)
            
    # Check 3: Practice count (10 sessions)
    if PracticeSession.objects.filter(user=user, is_correct=True).count() >= 10:
        grind_badge, _ = Achievement.objects.get_or_create(
            slug='ten-pack',
            defaults={'name': 'Dedicated Learner', 'description': 'Successfully practiced 10 shortcuts.', 'badge_icon': 'award', 'xp_reward': 150}
        )
        if not UserAchievement.objects.filter(user=user, achievement=grind_badge).exists():
            UserAchievement.objects.create(user=user, achievement=grind_badge)
            user.xp += grind_badge.xp_reward
            unlocked_achievements.append(grind_badge.name)
            
    user.save()
    
    return JsonResponse({
        'status': 'success',
        'xp_earned': xp_earned,
        'new_xp': user.xp,
        'level': user.level,
        'streak': user.streak,
        'leveled_up': leveled_up,
        'unlocked_achievements': unlocked_achievements
    })
