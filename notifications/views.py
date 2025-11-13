from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseBadRequest
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.utils import timezone
from django.core.paginator import Paginator
import json
from .models import Notification, NotificationSettings, WebPushSubscription
from .utils import send_notification


@login_required
def notifications(request):
    """User notifications page"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Mark all as read
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return redirect('notifications:notifications')
    
    context = {
        'page_obj': page_obj,
        'unread_count': Notification.objects.filter(user=request.user, is_read=False).count(),
    }
    
    return render(request, 'notifications/notifications.html', context)


@login_required
@csrf_exempt
def mark_read(request, notification_id):
    """Mark notification as read via AJAX"""
    try:
        notification = Notification.objects.get(
            id=notification_id,
            user=request.user
        )
        notification.mark_as_read()
        return JsonResponse({'status': 'success'})
    except Notification.DoesNotExist:
        return JsonResponse({'status': 'error', 'message': 'Notification not found'})


@login_required
@csrf_exempt
def mark_all_read(request):
    """Mark all notifications as read via AJAX"""
    Notification.objects.filter(user=request.user, is_read=False).update(
        is_read=True,
        read_at=timezone.now()
    )
    return JsonResponse({'status': 'success'})


@login_required
def notification_settings(request):
    """Notification settings page"""
    try:
        settings = request.user.notification_settings
    except NotificationSettings.DoesNotExist:
        settings = NotificationSettings.objects.create(user=request.user)
    
    if request.method == 'POST':
        # Update settings
        settings.email_bid_updates = request.POST.get('email_bid_updates') == 'on'
        settings.email_messages = request.POST.get('email_messages') == 'on'
        settings.email_payments = request.POST.get('email_payments') == 'on'
        settings.email_promotions = request.POST.get('email_promotions') == 'on'
        settings.email_system = request.POST.get('email_system') == 'on'
        
        settings.push_bid_updates = request.POST.get('push_bid_updates') == 'on'
        settings.push_messages = request.POST.get('push_messages') == 'on'
        settings.push_payments = request.POST.get('push_payments') == 'on'
        settings.push_promotions = request.POST.get('push_promotions') == 'on'
        settings.push_system = request.POST.get('push_system') == 'on'
        
        settings.sms_payments = request.POST.get('sms_payments') == 'on'
        settings.sms_urgent = request.POST.get('sms_urgent') == 'on'
        
        settings.save()
        return redirect('notifications:notification_settings')
    
    context = {
        'settings': settings,
    }
    
    return render(request, 'notifications/notification_settings.html', context)


@login_required
def get_unread_count(request):
    """Get unread notification count via AJAX"""
    count = Notification.objects.filter(user=request.user, is_read=False).count()
    return JsonResponse({'count': count})


@csrf_exempt
@login_required
@require_POST
def save_push_subscription(request):
    """Save or update a web push subscription for the current user"""
    try:
        payload = json.loads(request.body.decode('utf-8'))
        endpoint = payload['endpoint']
        keys = payload.get('keys', {})
        auth_key = keys.get('auth')
        p256dh_key = keys.get('p256dh')
        user_agent = payload.get('user_agent', '')
    except (json.JSONDecodeError, KeyError):
        return HttpResponseBadRequest('Invalid subscription payload')

    if not endpoint or not auth_key or not p256dh_key:
        return HttpResponseBadRequest('Missing subscription keys')

    WebPushSubscription.objects.update_or_create(
        user=request.user,
        endpoint=endpoint,
        defaults={
            'auth_key': auth_key,
            'p256dh_key': p256dh_key,
            'user_agent': user_agent or request.META.get('HTTP_USER_AGENT', ''),
        }
    )

    return JsonResponse({'status': 'success'})


@csrf_exempt
@login_required
@require_POST
def delete_push_subscription(request):
    """Delete a web push subscription for the current user"""
    try:
        payload = json.loads(request.body.decode('utf-8'))
        endpoint = payload['endpoint']
    except (json.JSONDecodeError, KeyError):
        return HttpResponseBadRequest('Invalid subscription payload')

    WebPushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()

    return JsonResponse({'status': 'success'})


# Utility functions for sending notifications
def send_bid_accepted_notification(bid):
    """Send notification when bid is accepted"""
    send_notification(
        user=bid.user,
        title='Bid Accepted!',
        message=f'Your bid for {bid.title} has been accepted by {bid.accepted_by.username}',
        notification_type='BID_ACCEPTED',
        related_object_type='bid',
        related_object_id=bid.id
    )


def send_new_message_notification(sender, recipient, bid, message):
    """Send notification for new message"""
    send_notification(
        user=recipient,
        title='New Message',
        message=f'{sender.username} sent you a message about {bid.title}',
        notification_type='NEW_MESSAGE',
        related_object_type='bid',
        related_object_id=bid.id
    )


def send_payment_notification(user, amount, transaction_type, description):
    """Send payment notification"""
    send_notification(
        user=user,
        title='Payment Update',
        message=f'{description}: ${amount}',
        notification_type='PAYMENT_RECEIVED' if transaction_type == 'BID_PAYMENT' else 'PAYMENT_SENT',
        related_object_type='transaction'
    )


def send_referral_bonus_notification(user, amount, referred_user):
    """Send referral bonus notification"""
    send_notification(
        user=user,
        title='Referral Bonus!',
        message=f'You earned ${amount} for referring {referred_user.username}',
        notification_type='REFERRAL_BONUS',
        related_object_type='user',
        related_object_id=referred_user.id
    )
