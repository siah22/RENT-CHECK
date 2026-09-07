from django.urls import path

from . import views

app_name = "properties"

urlpatterns = [
    path("", views.browse_properties, name="browse"),
    path("mine/", views.my_properties, name="my_properties"),
    path("new/", views.create_property, name="create"),
    path("<int:pk>/", views.property_detail, name="detail"),
    path("<int:pk>/edit/", views.edit_property, name="edit"),
    path("<int:pk>/delete/", views.delete_property, name="delete"),
    path("<int:pk>/toggle-rented/", views.toggle_rented, name="toggle_rented"),
    path("image/<int:pk>/delete/", views.delete_property_image, name="delete_image"),
]
