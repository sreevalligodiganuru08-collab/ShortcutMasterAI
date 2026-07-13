from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from core.views import custom_404

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('core.urls')),
    path('shortcuts/', include('shortcuts.urls')),
    path('practice/', include('practice.urls')),
    path('analytics/', include('analytics.urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

# Custom handler for 404
handler404 = custom_404
