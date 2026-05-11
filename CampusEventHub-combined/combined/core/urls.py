from django.urls import path
from . import views

urlpatterns = [
    # Home
    path('', views.home, name='home'),

    # Member 2 — Event browsing
    path('events/', views.event_list, name='event_list'),
    path('events/<int:event_id>/', views.event_detail, name='event_detail'),
    path('events/<int:event_id>/register/', views.register_event_view, name='register_event'),

    # Member 1 — Authentication
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('forgot-password/', views.forgot_password_view, name='forgot_password'),

    # Member 1 — User profile
    path('profile/', views.profile_view, name='profile'),
    path('my-events/', views.my_events_view, name='my_events'),

    # Admin auth
    path('admin-login/', views.admin_login_view, name='admin_login'),
    path('admin-logout/', views.admin_logout_view, name='admin_logout'),

    # Admin event management
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-monitoring/', views.admin_event_monitoring_view, name='admin_event_monitoring'),
    path('admin-events/', views.admin_event_list_view, name='admin_event_list'),
    path('admin-events/add/', views.add_event_view, name='add_event'),
    path('admin-events/<int:event_id>/edit/', views.edit_event_view, name='edit_event'),
    path('admin-events/<int:event_id>/delete/', views.delete_event_view, name='delete_event'),

    path('test/', views.test, name='test'),
]
