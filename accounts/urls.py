from django.urls import path

from . import views

app_name = "accounts"

urlpatterns = [
    path("register/", views.register, name="register"),
    path("login/", views.RentCheckLoginView.as_view(), name="login"),
    path("logout/", views.RentCheckLogoutView.as_view(), name="logout"),
    path("profile/", views.profile, name="profile"),
]
