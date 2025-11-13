from django.db import models
from django.utils import timezone
from accounts.models import User


class Notification(models.Model):
    """User notifications"""
    
    NOTIFICATION_TYPE_CHOICES = [
        ('BID_ACCEPTED', 'Bid Accepted'),
        ('BID_CANCELLED', 'Bid Cancelled'),
        ('NEW_MESSAGE', 'New Message'),
        ('PAYMENT_RECEIVED', 'Payment Received'),
        ('PAYMENT_SENT', 'Payment Sent'),
        ('WITHDRAWAL_PROCESSED', 'Withdrawal Processed'),
        ('REFERRAL_BONUS', 'Referral Bonus'),
        ('PREMIUM_EXPIRING', 'Premium Expiring'),
        ('EVENT_REMINDER', 'Event Reminder'),
        ('SYSTEM_ANNOUNCEMENT', 'System Announcement'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES)
    
    # Related object reference
    related_object_type = models.CharField(max_length=50, blank=True)  # e.g., 'bid', 'transaction'
    related_object_id = models.PositiveIntegerField(null=True, blank=True)
    
    # Status
    is_read = models.BooleanField(default=False)
    is_sent = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    read_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()
    
    def mark_as_sent(self):
        """Mark notification as sent"""
        self.is_sent = True
        self.save()


class NotificationSettings(models.Model):
    """User notification preferences"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='notification_settings')
    
    # Email notifications
    email_bid_updates = models.BooleanField(default=True)
    email_messages = models.BooleanField(default=True)
    email_payments = models.BooleanField(default=True)
    email_promotions = models.BooleanField(default=True)
    email_system = models.BooleanField(default=True)
    
    # Push notifications
    push_bid_updates = models.BooleanField(default=True)
    push_messages = models.BooleanField(default=True)
    push_payments = models.BooleanField(default=True)
    push_promotions = models.BooleanField(default=False)
    push_system = models.BooleanField(default=True)
    
    # SMS notifications
    sms_payments = models.BooleanField(default=False)
    sms_urgent = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Notification Settings"


class WebPushSubscription(models.Model):
    """Store web push subscriptions (VAPID) for users"""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='webpush_subscriptions')
    endpoint = models.URLField(unique=True)
    auth_key = models.CharField(max_length=256)
    p256dh_key = models.CharField(max_length=256)
    user_agent = models.CharField(max_length=512, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Web Push Subscription"
        verbose_name_plural = "Web Push Subscriptions"
        ordering = ['-created_at']

    def __str__(self):
        return f"WebPush subscription for {self.user.username}"