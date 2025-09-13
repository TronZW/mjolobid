from django.urls import path
from . import views

app_name = 'notifications'

urlpatterns = [
    path('', views.notifications, name='notifications'),
    path('mark-read/<int:notification_id>/', views.mark_read, name='mark_read'),
    path('mark-all-read/', views.mark_all_read, name='mark_all_read'),
    path('settings/', views.notification_settings, name='notification_settings'),
    path('api/unread-count/', views.get_unread_count, name='unread_count'),
]
