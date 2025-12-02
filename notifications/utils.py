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
    
    # Send email notification first (most reliable method)
    # Email notifications are enabled by default for bids and messages
    should_send = _should_send_email_notification(notification_type, settings)
    print(f"DEBUG: Notification type: {notification_type}, Should send email: {should_send}")
    if should_send:
        print(f"DEBUG: Attempting to send email notification to {user.username} ({user.email})")
        send_email_notification(user, notification)
    else:
        print(f"DEBUG: Email notification skipped for {notification_type}")
    
    # Send real-time notification via WebSocket and Push (optional, less reliable)
    if _should_send_push_notification(notification_type, settings):
        send_websocket_notification(user, notification)
        send_web_push_notification(user, notification)
    
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
        print("Web push not available: pywebpush not installed")
        return

    vapid_public_key = getattr(settings, 'WEBPUSH_VAPID_PUBLIC_KEY', '')
    vapid_private_key = getattr(settings, 'WEBPUSH_VAPID_PRIVATE_KEY', '')
    vapid_contact_email = getattr(settings, 'WEBPUSH_VAPID_CONTACT_EMAIL', '')

    if not vapid_public_key or not vapid_private_key:
        print(f"Web push not configured: public_key={bool(vapid_public_key)} (length: {len(vapid_public_key) if vapid_public_key else 0}), private_key={bool(vapid_private_key)} (length: {len(vapid_private_key) if vapid_private_key else 0})")
        return

    payload = {
        'title': notification.title,
        'body': notification.message,
        'url': notification_payload_url(notification),
        'tag': f"{notification.notification_type}-{notification.id}",
        'data': {
            'notification_id': notification.id,
            'type': notification.notification_type,
        },
    }

    subscriptions = WebPushSubscription.objects.filter(user=user)
    if not subscriptions.exists():
        print(f"No push subscriptions found for user {user.username}")
        return
    
    print(f"Sending push notification to {subscriptions.count()} subscription(s) for user {user.username}")

    for subscription in subscriptions:
        try:
            # pywebpush 2.x API - only needs vapid_private_key and vapid_claims
            # The public key is derived from the private key automatically
            vapid_claims = {
                "sub": f"mailto:{vapid_contact_email}" if vapid_contact_email else "mailto:support@mjolobid.com"
            }
            
            print(f"Attempting to send push notification to {subscription.endpoint[:50]}...")
            print(f"VAPID private key length: {len(vapid_private_key)}")
            print(f"Payload: {json.dumps(payload)}")
            
            result = webpush(
                subscription_info={
                    "endpoint": subscription.endpoint,
                    "keys": {
                        "p256dh": subscription.p256dh_key,
                        "auth": subscription.auth_key,
                    },
                },
                data=json.dumps(payload),
                vapid_private_key=vapid_private_key,
                vapid_claims=vapid_claims,
            )
            print(f"Push notification sent successfully! Response: {result}")
        except WebPushException as exc:
            # Remove stale subscriptions (410 Gone or 404 Not Found)
            status = getattr(exc.response, 'status_code', None)
            if status in (404, 410):
                print(f"Removing stale subscription (status {status}): {subscription.endpoint[:50]}...")
                subscription.delete()
            else:
                print(f"Web push failed for {subscription.endpoint[:50]}...: {exc}")
                import traceback
                traceback.print_exc()
        except Exception as exc:
            print(f"Unexpected web push error for {subscription.endpoint[:50]}...: {exc}")
            import traceback
            traceback.print_exc()


def notification_payload_url(notification):
    """Determine a reasonable URL to open when a notification is clicked."""
    from django.conf import settings as django_settings
    
    base_url = getattr(django_settings, 'SITE_URL', 'http://localhost:8000')
    if not base_url.startswith('http'):
        base_url = f'http://{base_url}'
    
    # Build the target URL
    if notification.related_object_type == 'conversation' and notification.related_object_id:
        target_path = f"/messaging/conversation/{notification.related_object_id}/"
    elif notification.related_object_type == 'bid' and notification.related_object_id:
        target_path = f"/bids/bid/{notification.related_object_id}/"
    elif notification.related_object_type == 'offer' and notification.related_object_id:
        target_path = f"/offers/offer/{notification.related_object_id}/"
    elif notification.related_object_type == 'transaction' and notification.related_object_id:
        target_path = f"/payments/wallet/"
    else:
        target_path = "/notifications/"
    
    # Return URL with login redirect - if user is not logged in, they'll be redirected to login first
    # Django's @login_required will handle the redirect automatically
    return f"{base_url}{target_path}"


def send_email_notification(user, notification):
    """Send email notification with scenario-specific content"""
    from django.core.mail import send_mail, EmailMultiAlternatives
    from django.template.loader import render_to_string
    from django.conf import settings as django_settings
    from django.utils import timezone
    
    try:
        # Get user's email
        user_email = user.email
        if not user_email:
            print(f"Cannot send email notification: User {user.username} has no email address")
            return
        
        # Build notification URL (already includes full URL with domain)
        full_url = notification_payload_url(notification)
        base_url = getattr(django_settings, 'SITE_URL', 'http://localhost:8000')
        if not base_url.startswith('http'):
            base_url = f'http://{base_url}'
        
        # Determine subject based on notification type (keep it simple like before)
        if notification.notification_type == 'NEW_MESSAGE':
            # Extract sender name from message
            message_text = notification.message
            if ' sent you a message' in message_text:
                sender_name = message_text.split(' sent you a message')[0]
                subject = f'New message from {sender_name} - MjoloBid'
            elif ' sent you a message in' in message_text:
                sender_name = message_text.split(' sent you a message in')[0]
                subject = f'New message from {sender_name} - MjoloBid'
            else:
                subject = f'New message received - MjoloBid'
        elif notification.notification_type == 'OFFER_BID':
            subject = f'{notification.title} - MjoloBid'
        elif notification.notification_type == 'OFFER_ACCEPTED':
            subject = f'Your bid has been selected - MjoloBid'
        elif notification.notification_type == 'BID_ACCEPTED':
            subject = f'Your bid has been accepted - MjoloBid'
        else:
            subject = f'{notification.title} - MjoloBid'
        
        # Try to fetch related objects for template context (but don't fail if they don't exist)
        bid = None
        offer = None
        conversation = None
        sender_username = None
        
        if notification.related_object_type == 'bid' and notification.related_object_id:
            try:
                from bids.models import Bid
                bid = Bid.objects.select_related('user', 'event_category', 'accepted_by').get(id=notification.related_object_id)
            except:
                pass
        
        if notification.related_object_type == 'offer' and notification.related_object_id:
            try:
                from offers.models import Offer
                offer = Offer.objects.select_related('user', 'event_category', 'accepted_by').get(id=notification.related_object_id)
            except:
                pass
        
        if notification.related_object_type == 'conversation' and notification.related_object_id:
            try:
                from messaging.models import Conversation
                conversation = Conversation.objects.prefetch_related('participants').get(id=notification.related_object_id)
                # Get other participant (sender)
                for participant in conversation.participants.all():
                    if participant.id != user.id:
                        sender_username = participant.username
                        break
            except:
                pass
        
        # Extract sender username from message if not found from conversation
        if not sender_username and notification.notification_type == 'NEW_MESSAGE':
            if ' sent you a message' in notification.message:
                sender_username = notification.message.split(' sent you a message')[0]
            elif ' sent you a message in' in notification.message:
                sender_username = notification.message.split(' sent you a message in')[0]
        
        # Determine email scenario for template (but don't fail if detection fails)
        message_lower = notification.message.lower()
        email_scenario = 'default'
        button_text = 'View Details'
        button_url = full_url
        
        if notification.notification_type == 'NEW_MESSAGE':
            email_scenario = 'new_message'
            button_text = 'Reply to Message'
        elif notification.notification_type == 'BID_ACCEPTED':
            email_scenario = 'bid_accepted'
            button_text = 'View Acceptances & Choose'
            if bid:
                button_url = f"{base_url}/bids/bid/{bid.id}/"
        elif notification.notification_type == 'OFFER_ACCEPTED':
            email_scenario = 'offer_accepted'
            button_text = 'Start Conversation'
            if offer:
                button_url = f"{base_url}/messaging/start-offer/{offer.id}/"
        elif 'viewed your bid' in message_lower:
            email_scenario = 'bid_viewed'
            button_text = 'View Your Bid'
        elif 'viewed your offer' in message_lower or ('viewed your' in message_lower and offer):
            email_scenario = 'offer_viewed'
            button_text = 'View Your Offer'
        elif 'posted a new bid' in message_lower:
            email_scenario = 'new_bid_posted'
            button_text = 'View Bid & Accept'
        elif 'created a new offer' in message_lower:
            email_scenario = 'new_offer_posted'
            button_text = 'View Offer & Place Bid'
        elif 'placed a' in message_lower and 'bid on your offer' in message_lower:
            email_scenario = 'bid_on_offer'
            button_text = 'View Bids on Your Offer'
            if offer:
                button_url = f"{base_url}/offers/offer/{offer.id}/bids/"
        
        # Get recipient name
        recipient_name = user.get_full_name() or user.username
        
        # Prepare email context (keep it simple, template will handle missing data)
        context = {
            'user': user,
            'notification': notification,
            'title': notification.title,
            'message': notification.message,
            'notification_url': full_url,
            'button_url': button_url,
            'button_text': button_text,
            'site_name': 'MjoloBid',
            'site_url': base_url,
            'email_scenario': email_scenario,
            'bid': bid,
            'offer': offer,
            'conversation': conversation,
            'recipient_name': recipient_name,
            'sender_username': sender_username or 'Someone',
            'viewer_username': notification.message.split(' viewed')[0] if ' viewed' in notification.message else None,
            'accepter_username': (notification.message.split(' has accepted your bid')[0] if ' has accepted your bid' in notification.message else None) or (notification.message.split(' has selected your bid')[0] if ' has selected your bid' in notification.message else None),
            'bid_creator_username': bid.user.username if bid and bid.user else None,
            'offer_creator_username': offer.user.username if offer and offer.user else None,
        }
        
        # Render email templates with scenario-specific content
        html_message = render_to_string('emails/notification.html', context)
        text_message = render_to_string('emails/notification.txt', context)
        
        # Send email with improved headers for better deliverability
        email = EmailMultiAlternatives(
            subject=subject,
            body=text_message,
            from_email=getattr(django_settings, 'DEFAULT_FROM_EMAIL', 'noreply@mjolobid.com'),
            to=[user_email],
            headers={
                'X-Mailer': 'MjoloBid Notification System',
                'X-Priority': '3',  # Normal priority
                'X-MSMail-Priority': 'Normal',
                'Importance': 'Normal',
                'List-Unsubscribe': f'<{base_url}/notifications/unsubscribe/>',
                'List-Unsubscribe-Post': 'List-Unsubscribe=One-Click',
                'Message-ID': f'<notification-{notification.id}-{int(timezone.now().timestamp())}@mjolobid.com>',
                'Reply-To': getattr(django_settings, 'DEFAULT_FROM_EMAIL', 'noreply@mjolobid.com'),
            }
        )
        email.attach_alternative(html_message, "text/html")
        email.send(fail_silently=False)
        
        # Mark notification as sent
        notification.mark_as_sent()
        print(f"Email notification sent successfully to {user_email} for notification: {notification.title}")
        
    except Exception as e:
        error_msg = str(e)
        print(f"Failed to send email notification to {user.username}: {error_msg}")
        
        # Provide helpful error messages
        if 'BadCredentials' in error_msg or 'Authentication failed' in error_msg or '535' in error_msg:
            print("\n⚠️  Email authentication failed. For Gmail:")
            print("   1. Enable 2-Factor Authentication on your Google account")
            print("   2. Generate an 'App Password' at: https://myaccount.google.com/apppasswords")
            print("   3. Use the App Password (16 characters, no spaces) instead of your regular password")
            print("   4. Make sure EMAIL_HOST_USER is your full Gmail address (mjolobidapp@gmail.com)")
            print("   5. Update EMAIL_HOST_PASSWORD in settings.py with the App Password")
        elif 'Connection refused' in error_msg or 'Connection timed out' in error_msg:
            print("\n⚠️  Could not connect to email server. Check:")
            print("   - EMAIL_HOST is correct (smtp.gmail.com for Gmail)")
            print("   - EMAIL_PORT is correct (587 for TLS)")
            print("   - Your internet connection")
        else:
            import traceback
            traceback.print_exc()
        
        # Don't mark as sent if email failed, but notification is still created in database


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
    elif notification_type in ['OFFER_BID', 'OFFER_ACCEPTED'] and settings.push_bid_updates:
        return True
    elif notification_type in ['PAYMENT_RECEIVED', 'PAYMENT_SENT'] and settings.push_payments:
        return True
    elif notification_type == 'SYSTEM_ANNOUNCEMENT' and settings.push_system:
        return True
    return False


def _should_send_email_notification(notification_type, settings):
    """Check if email notification should be sent"""
    # Email notifications are enabled by default for bids and messages
    # Always send emails for important events regardless of settings
    if notification_type == 'BID_ACCEPTED':
        return True  # Always send for bid accepted
    elif notification_type == 'NEW_MESSAGE':
        return True  # Always send for new messages
    elif notification_type == 'OFFER_BID':
        return True  # Always send for bid viewed, new bids, new offers
    elif notification_type == 'OFFER_ACCEPTED':
        return True  # Always send for offer accepted
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
