from django.urls import path
from . import views

app_name = 'properties'

urlpatterns = [
    path('', views.browse_properties, name='browse'),
    path('create/', views.property_create, name='create'),
    path('new/', views.property_create, name='new'),
    path('my/', views.my_properties, name='my_properties'),
    path('<int:pk>/', views.property_detail, name='detail'),
    path('<int:pk>/edit/', views.property_edit, name='edit'),
    path('<int:pk>/delete/', views.property_delete, name='delete'),
    path('<int:pk>/toggle-rented/', views.property_toggle_rented, name='toggle_rented'),
    path('image/<int:pk>/delete/', views.property_delete_image, name='delete_image'),
]