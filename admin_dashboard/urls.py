from django.urls import path
from . import views

app_name = 'admin_dashboard'

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('users/', views.users_analytics, name='users_analytics'),
    path('bids/', views.bids_analytics, name='bids_analytics'),
    path('revenue/', views.revenue_analytics, name='revenue_analytics'),
    path('api/metrics/', views.api_metrics, name='api_metrics'),
]
