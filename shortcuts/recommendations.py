import random
from shortcuts.models import Shortcut
from practice.models import PracticeSession
from django.db.models import Count

def get_recommendations(user, limit=3):
    """
    AI Recommendation Logic:
    1. Identify shortcuts the user has practiced but has low accuracy (< 80%).
    2. Suggest unpracticed shortcuts in the user's most active category.
    3. Suggest shortcuts that save the most time overall.
    """
    if not user.is_authenticated:
        # For anonymous users, return top time-saving shortcuts
        return Shortcut.objects.order_by('-estimated_time_saved')[:limit]

    user_sessions = PracticeSession.objects.filter(user=user)
    practiced_ids = user_sessions.values_list('shortcut_id', flat=True).distinct()
    
    recommendations = []

    # 1. Weak shortcuts (accuracy < 80%)
    if user_sessions.exists():
        weak_shortcuts = []
        for s_id in practiced_ids:
            sessions = user_sessions.filter(shortcut_id=s_id)
            avg_acc = sum([s.accuracy for s in sessions]) / len(sessions)
            if avg_acc < 80.0:
                weak_shortcuts.append(s_id)
        
        if weak_shortcuts:
            recommendations.extend(
                list(Shortcut.objects.filter(id__in=weak_shortcuts)[:limit])
            )

    # 2. Most active category unpracticed shortcuts
    if len(recommendations) < limit and user_sessions.exists():
        fav_cat_data = user_sessions.values('shortcut__category') \
                                    .annotate(count=Count('id')) \
                                    .order_by('-count')
        if fav_cat_data:
            fav_cat = fav_cat_data[0]['shortcut__category']
            cat_shortcuts = Shortcut.objects.filter(category=fav_cat).exclude(id__in=practiced_ids)
            recommendations.extend(list(cat_shortcuts[:limit - len(recommendations)]))

    # 3. Fallback: High time-savers
    if len(recommendations) < limit:
        exclude_ids = [r.id for r in recommendations]
        high_savers = Shortcut.objects.exclude(id__in=exclude_ids).order_by('-estimated_time_saved')
        recommendations.extend(list(high_savers[:limit - len(recommendations)]))

    return recommendations[:limit]
