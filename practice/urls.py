from django.urls import path
from . import views

app_name = 'practice'

urlpatterns = [
    path('', views.practice_home, name='home'),
    path('session/', views.practice_session, name='session'),
    path('quiz/', views.practice_quiz, name='quiz'),
    path('daily-challenge/', views.daily_challenge, name='daily_challenge'),
    path('log/', views.log_practice, name='log_practice'),
]
