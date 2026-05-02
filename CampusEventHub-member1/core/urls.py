from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('test/', views.test, name='test'),

    # Member 1 — Authentication & User Profile
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),
    path('profile/', views.profile_view, name='profile'),
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('admin-logout/', views.admin_logout_view, name='admin_logout'),
    path('my-events/', views.my_events_view, name='my_events'),

    # Existing admin/event URLs retained for the base project.
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-monitoring/', views.admin_event_monitoring_view, name='admin_event_monitoring'),
    path('admin-events/', views.admin_event_list_view, name='admin_event_list'),
    path('admin-events/add/', views.add_event_view, name='add_event'),
    path('admin-events/<int:event_id>/edit/', views.edit_event_view, name='edit_event'),
    path('admin-events/<int:event_id>/delete/', views.delete_event_view, name='delete_event'),

    # Merge-friendly aliases matching the shared naming convention.
    path('admin-events/add/', views.add_event_view, name='admin_event_add'),
    path('admin-events/<int:event_id>/edit/', views.edit_event_view, name='admin_event_edit'),
    path('admin-monitoring/', views.admin_event_monitoring_view, name='admin_event_monitor'),
]
