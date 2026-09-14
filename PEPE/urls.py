from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),

    # Home page, dashboard, etc.
    path('', include('core.urls')),

    # Account management (login, register, logout, profile)
    path('accounts/', include('accounts.urls')),

    # Properties application routes
    path('properties/', include('properties.urls')),

    # Favorites, inquiries, viewings, bookings, reviews, notifications
    path('engagement/', include('engagement.urls')),
]

# Serve user-uploaded media files (property images) during development and testing
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)