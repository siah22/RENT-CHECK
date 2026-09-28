from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls.i18n import i18n_patterns
from django.urls import include, path

from payments import views as payment_views

urlpatterns = [
    path("admin/", admin.site.urls),
    path("i18n/", include("django.conf.urls.i18n")),
    # M-Pesa confirmation callback lives OUTSIDE i18n_patterns and without CSRF
    # so the operator's server can always reach it at a fixed path.
    path("payments/callback/<str:token>/", payment_views.mpesa_callback),
]

urlpatterns += i18n_patterns(
    path("", include("core.urls")),
    path("accounts/", include("accounts.urls")),
    path("properties/", include("properties.urls")),
    path("engagement/", include("engagement.urls")),
    path("payments/", include("payments.urls")),
    prefix_default_language=False,
)

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
