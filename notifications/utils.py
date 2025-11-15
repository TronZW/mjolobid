from django.utils import timezone
from django.conf import settings
from .models import Notification, NotificationSettings, WebPushSubscription
import json

# Try to import channels, but don't fail if it's not available
try:
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    CHANNELS_AVAILABLE = True
except ImportError:
    CHANNELS_AVAILABLE = False

# Try to import pywebpush for web push notifications
try:
    from pywebpush import webpush, WebPushException
    WEBPUSH_AVAILABLE = True
except ImportError:
    WEBPUSH_AVAILABLE = False


def send_notification(user, title, message, notification_type, related_object_type='', related_object_id=None):
    """Send notification to user"""
    
    # Create notification in database
    notification = Notification.objects.create(
        user=user,
        title=title,
        message=message,
        notification_type=notification_type,
        related_object_type=related_object_type,
        related_object_id=related_object_id
    )
    
    # Get user's notification settings
    try:
        settings = user.notification_settings
    except NotificationSettings.DoesNotExist:
        settings = NotificationSettings.objects.create(user=user)
    
    # Send real-time notification via WebSocket
    if _should_send_push_notification(notification_type, settings):
        send_websocket_notification(user, notification)
        send_web_push_notification(user, notification)
    
    # Send email notification (if enabled)
    if _should_send_email_notification(notification_type, settings):
        send_email_notification(user, notification)
    
    # Send SMS notification (if enabled)
    if _should_send_sms_notification(notification_type, settings):
        send_sms_notification(user, notification)
    
    return notification


def send_websocket_notification(user, notification):
    """Send notification via WebSocket"""
    if not CHANNELS_AVAILABLE:
        # Skip WebSocket notification if channels is not available
        return
    
    try:
        channel_layer = get_channel_layer()
        
        async_to_sync(channel_layer.group_send)(
            f'notifications_{user.id}',
            {
                'type': 'notification_message',
                'message': notification.message,
                'title': notification.title,
                'notification_type': notification.notification_type,
                'timestamp': timezone.now().isoformat(),
            }
        )
    except Exception as e:
        # Log error but don't fail the notification
        print(f"WebSocket notification failed: {e}")
        pass


def send_web_push_notification(user, notification):
    """Send push notification using the Web Push protocol"""
    if not WEBPUSH_AVAILABLE:
        return

    vapid_public_key = getattr(settings, 'WEBPUSH_VAPID_PUBLIC_KEY', '')
    vapid_private_key = getattr(settings, 'WEBPUSH_VAPID_PRIVATE_KEY', '')
    vapid_contact_email = getattr(settings, 'WEBPUSH_VAPID_CONTACT_EMAIL', '')

    if not vapid_public_key or not vapid_private_key:
        return

    # Use a simple SVG icon as data URL (works everywhere)
    # This is a purple bell icon in SVG format
    icon_url = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iNjQiIGhlaWdodD0iNjQiIHZpZXdCb3g9IjAgMCA2NCA2NCIgZmlsbD0ibm9uZSIgeG1sbnM9Imh0dHA6Ly93d3cudzMub3JnLzIwMDAvc3ZnIj4KPGNpcmNsZSBjeD0iMzIiIGN5PSIzMiIgcj0iMzIiIGZpbGw9IiM4QjVDRjYiLz4KPHBhdGggZD0iTTMyIDIwQzI2LjQ3NzEgMjAgMjIgMjQuNDc3MSAyMiAzMEMyMiAzNS41MjI5IDI2LjQ3NzEgNDAgMzIgNDBDMzcuNTIyOSA0MCA0MiAzNS41MjI5IDQyIDMwQzQyIDI0LjQ3NzEgMzcuNTIyOSAyMCAzMiAyMFoiIGZpbGw9IndoaXRlIi8+Cjwvc3ZnPgo='
    
    payload = {
        'title': notification.title,
        'body': notification.message,
        'url': notification_payload_url(notification),
        'tag': f"{notification.notification_type}-{notification.id}",
        'icon': icon_url,
        'badge': icon_url,
        'vibrate': [200, 100, 200],
        'data': {
            'notification_id': notification.id,
            'type': notification.notification_type,
            'url': notification_payload_url(notification),
        },
    }

    subscriptions = WebPushSubscription.objects.filter(user=user)
    for subscription in subscriptions:
        try:
            webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {
                        "p256dh": subscription.p256dh_key,
                        "auth": subscription.auth_key,
                    },
                },
                data=json.dumps(payload),
                vapid_private_key=vapid_private_key,
                vapid_public_key=vapid_public_key,
                vapid_claims={"sub": f"mailto:{vapid_contact_email}"} if vapid_contact_email else None,
            )
        except WebPushException as exc:
            # Remove stale subscriptions (410 Gone or 404 Not Found)
            status = getattr(exc.response, 'status_code', None)
            if status in (404, 410):
                subscription.delete()
            else:
                print(f"Web push failed: {exc}")
        except Exception as exc:
            print(f"Unexpected web push error: {exc}")


def notification_payload_url(notification):
    """Determine a reasonable URL to open when a notification is clicked."""
    if notification.related_object_type == 'bid' and notification.related_object_id:
        return f"/bids/bid/{notification.related_object_id}/"
    if notification.related_object_type == 'offer' and notification.related_object_id:
        return f"/offers/offer/{notification.related_object_id}/"
    if notification.related_object_type == 'transaction' and notification.related_object_id:
        return f"/payments/wallet/"
    return "/notifications/"


def send_email_notification(user, notification):
    """Send email notification"""
    # TODO: Implement email sending
    # For now, just mark as sent
    notification.mark_as_sent()
    pass


def send_sms_notification(user, notification):
    """Send SMS notification"""
    # TODO: Implement SMS sending
    # For now, just mark as sent
    notification.mark_as_sent()
    pass


def _should_send_push_notification(notification_type, settings):
    """Check if push notification should be sent"""
    if notification_type == 'BID_ACCEPTED' and settings.push_bid_updates:
        return True
    elif notification_type == 'NEW_MESSAGE' and settings.push_messages:
        return True
    elif notification_type in ['PAYMENT_RECEIVED', 'PAYMENT_SENT'] and settings.push_payments:
        return True
    elif notification_type == 'SYSTEM_ANNOUNCEMENT' and settings.push_system:
        return True
    return False


def _should_send_email_notification(notification_type, settings):
    """Check if email notification should be sent"""
    if notification_type == 'BID_ACCEPTED' and settings.email_bid_updates:
        return True
    elif notification_type == 'NEW_MESSAGE' and settings.email_messages:
        return True
    elif notification_type in ['PAYMENT_RECEIVED', 'PAYMENT_SENT'] and settings.email_payments:
        return True
    elif notification_type == 'SYSTEM_ANNOUNCEMENT' and settings.email_system:
        return True
    return False


def _should_send_sms_notification(notification_type, settings):
    """Check if SMS notification should be sent"""
    if notification_type in ['PAYMENT_RECEIVED', 'PAYMENT_SENT'] and settings.sms_payments:
        return True
    elif notification_type in ['BID_ACCEPTED', 'PAYMENT_RECEIVED'] and settings.sms_urgent:
        return True
    return False


def send_bulk_notification(users, title, message, notification_type):
    """Send notification to multiple users"""
    notifications = []
    for user in users:
        notification = send_notification(
            user=user,
            title=title,
            message=message,
            notification_type=notification_type
        )
        notifications.append(notification)
    return notifications


def send_admin_notification(message, notification_type='SYSTEM'):
    """Send notification to admin users"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    admin_users = User.objects.filter(is_staff=True)
    return send_bulk_notification(
        users=admin_users,
        title='Admin Notification',
        message=message,
        notification_type='SYSTEM_ANNOUNCEMENT'
    )
