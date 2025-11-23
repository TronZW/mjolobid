from django.conf import settings


def webpush_settings(request):
    """Expose web push settings to templates"""
    # Don't check server-side subscriptions - each browser has its own subscription
    # The JavaScript will check the actual browser subscription status
    return {
        'WEBPUSH_PUBLIC_KEY': getattr(settings, 'WEBPUSH_VAPID_PUBLIC_KEY', ''),
    }

