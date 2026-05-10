from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('test/', views.test, name='test'),

    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-monitoring/', views.admin_event_monitoring_view, name='admin_event_monitoring'),
    
    path('admin-events/', views.admin_event_list_view, name='admin_event_list'),
    path('admin-events/add/', views.add_event_view, name='add_event'),
    path('admin-events/<int:event_id>/edit/', views.edit_event_view, name='edit_event'),
    path('admin-events/<int:event_id>/delete/', views.delete_event_view, name='delete_event'),
]