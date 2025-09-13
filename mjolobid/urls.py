"""
URL configuration for mjolobid project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse

def health_check(request):
    try:
        # Simple health check that doesn't require database
        return JsonResponse({
            'status': 'healthy', 
            'message': 'MjoloBid is running!',
            'version': '1.0.0'
        })
    except Exception as e:
        return JsonResponse({
            'status': 'unhealthy', 
            'error': str(e)
        }, status=500)

def root_health_check(request):
    """Simple root endpoint for Railway healthcheck - no database required"""
    try:
        return JsonResponse({'status': 'ok', 'message': 'MjoloBid is running'})
    except Exception as e:
        # Even if there's an error, return 200 for health check
        return JsonResponse({'status': 'ok', 'error': str(e)})

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('bids/', include('bids.urls')),
    path('payments/', include('payments.urls')),
    path('notifications/', include('notifications.urls')),
    path('dashboard/', include('admin_dashboard.urls')),
    path('', root_health_check, name='root_health_check'),
    path('accounts/', include('accounts.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
