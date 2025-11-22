from django.conf import settings
from .models import WebPushSubscription


def webpush_settings(request):
    """Expose web push settings to templates"""
    has_push_subscription = False
    if request.user.is_authenticated:
        has_push_subscription = WebPushSubscription.objects.filter(user=request.user).exists()
    
    return {
        'WEBPUSH_PUBLIC_KEY': getattr(settings, 'WEBPUSH_VAPID_PUBLIC_KEY', ''),
        'HAS_PUSH_SUBSCRIPTION': has_push_subscription,
    }

