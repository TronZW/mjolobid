from django.utils import timezone
from .models import Notification, NotificationSettings
import json

# Try to import channels, but don't fail if it's not available
try:
    from channels.layers import get_channel_layer
    from asgiref.sync import async_to_sync
    CHANNELS_AVAILABLE = True
except ImportError:
    CHANNELS_AVAILABLE = False


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
