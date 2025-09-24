from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    path('login/', views.user_login, name='login'),
    path('logout/', views.user_logout, name='logout'),
    path('profile-setup/', views.profile_setup, name='profile_setup'),
    path('profile/', views.profile, name='profile'),
    path('edit-profile/', views.edit_profile, name='edit_profile'),
    path('premium/', views.premium_upgrade, name='premium_upgrade'),
    path('affiliate/', views.affiliate_dashboard, name='affiliate_dashboard'),
    path('update-location/', views.update_location, name='update_location'),
    path('rate-user/<int:user_id>/', views.rate_user, name='rate_user'),
    path('test-media/', views.test_media, name='test_media'),
]
