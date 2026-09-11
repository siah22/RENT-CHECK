from django.urls import path
from . import views

app_name = 'properties'

urlpatterns = [
    path('', views.browse_properties, name='browse'),
    path('create/', views.property_create, name='create'),
]