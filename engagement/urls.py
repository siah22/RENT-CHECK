from django.urls import path

from . import views

app_name = "engagement"

urlpatterns = [
    path("favorites/", views.favorite_list, name="favorite_list"),
    path("favorites/toggle/<int:pk>/", views.toggle_favorite, name="toggle_favorite"),

    path("inquiries/", views.inquiry_list, name="inquiry_list"),
    path("inquiries/new/<int:pk>/", views.send_inquiry, name="send_inquiry"),
    path("inquiries/<int:pk>/respond/", views.respond_inquiry, name="respond_inquiry"),

    path("viewings/", views.viewing_list, name="viewing_list"),
    path("viewings/new/<int:pk>/", views.request_viewing, name="request_viewing"),
    path("viewings/<int:pk>/status/<str:new_status>/", views.update_viewing_status, name="update_viewing_status"),

    path("bookings/", views.booking_list, name="booking_list"),
    path("bookings/new/<int:pk>/", views.request_booking, name="request_booking"),
    path("bookings/<int:pk>/status/<str:new_status>/", views.update_booking_status, name="update_booking_status"),

    path("reports/new/<int:pk>/", views.report_property, name="report_property"),
    path("reviews/new/<int:pk>/", views.add_review, name="add_review"),

    path("notifications/", views.notification_list, name="notification_list"),
    path("notifications/<int:pk>/delete/", views.notification_delete, name="notification_delete"),

    path("messages/", views.conversation_list, name="conversation_list"),
    path("messages/start/<int:pk>/", views.start_conversation, name="start_conversation"),
    path("messages/<int:pk>/", views.conversation_detail, name="conversation_detail"),
]
