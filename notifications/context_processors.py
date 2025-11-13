from django.conf import settings


def webpush_settings(request):
    """Expose web push settings to templates"""
    return {
        'WEBPUSH_PUBLIC_KEY': getattr(settings, 'WEBPUSH_VAPID_PUBLIC_KEY', ''),
    }

