from django.urls import path
from . import views

app_name = 'properties'

urlpatterns = [
    path('', views.browse_properties, name='browse'),
    path('<int:pk>/', views.property_detail, name='detail'),
    path('create/', views.property_create, name='create'),
    path('new/', views.property_create, name='new'),  # Handles clicks from "Create New Property"
]