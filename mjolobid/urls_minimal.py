"""
Minimal URL configuration for health check.
"""
from django.http import JsonResponse
from django.urls import path

def health_check(request):
    """Ultra-simple health check"""
    return JsonResponse({'status': 'ok'})

urlpatterns = [
    path('', health_check),
]
