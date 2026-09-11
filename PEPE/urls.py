from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView

urlpatterns = [
    # Admin interface
    path('admin/', admin.site.urls),
    
    # Properties application routes
    path('properties/', include('properties.urls')),
    
    # Redirect root URL ('/') directly to '/properties/'
    path('', RedirectView.as_view(url='/properties/', permanent=False)),
]

# Serve user-uploaded media files (property images) during development and testing
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)