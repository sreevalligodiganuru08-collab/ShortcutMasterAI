"""
URL configuration for shortcutmaster project.
"""

from django.urls import include, path

urlpatterns = [
    path("", include("trainer.urls")),
]
