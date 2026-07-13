from django.urls import path
from . import views

app_name = 'shortcuts'

urlpatterns = [
    path('', views.library, name='library'),
    path('<slug:app_slug>/', views.library, name='library_app'),
]
