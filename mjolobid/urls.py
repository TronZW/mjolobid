"""
URL configuration for mjolobid project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.generic import TemplateView
from accounts.views import home

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

urlpatterns = [
    path('admin/', admin.site.urls),
    path('health/', health_check, name='health_check'),
    path('service-worker.js', TemplateView.as_view(template_name='serviceworker.js', content_type='application/javascript'), name='service_worker'),
    path('bids/', include('bids.urls')),
    path('offers/', include('offers.urls')),
    path('payments/', include('payments.urls')),
    path('notifications/', include('notifications.urls')),
    path('messaging/', include('messaging.urls')),
    path('dashboard/', include('admin_dashboard.urls')),
    path('accounts/', include('accounts.urls')),
    path('', home, name='home'),  # Landing page at root URL
]

# Serve media files (for testing - files will be lost on restart)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

# Serve static files in development
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
