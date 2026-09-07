from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("dashboard/", views.dashboard, name="dashboard"),
    path("dashboard/properties/", views.dashboard_properties, name="dashboard_properties"),
    path("dashboard/properties/<int:pk>/<str:action>/", views.dashboard_property_action,
         name="dashboard_property_action"),
    path("dashboard/reports/", views.dashboard_reports, name="dashboard_reports"),
    path("dashboard/reports/<int:pk>/status/<str:new_status>/", views.dashboard_report_action,
         name="dashboard_report_action"),
    path("dashboard/users/", views.dashboard_users, name="dashboard_users"),
    path("dashboard/users/<int:pk>/toggle-status/", views.dashboard_toggle_user_status,
         name="dashboard_toggle_user_status"),
]
