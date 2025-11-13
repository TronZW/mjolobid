from django.contrib import admin
from .models import Notification, NotificationSettings, WebPushSubscription


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'notification_type', 'is_read', 'is_sent', 'created_at')
    list_filter = ('notification_type', 'is_read', 'is_sent', 'created_at')
    search_fields = ('user__username', 'title', 'message')
    raw_id_fields = ('user',)
    readonly_fields = ('created_at', 'read_at')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'message', 'notification_type')
        }),
        ('Related Object', {
            'fields': ('related_object_type', 'related_object_id')
        }),
        ('Status', {
            'fields': ('is_read', 'is_sent', 'read_at')
        }),
        ('Timestamps', {
            'fields': ('created_at',)
        }),
    )


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ('user', 'email_bid_updates', 'push_bid_updates', 'sms_payments')
    list_filter = ('email_bid_updates', 'push_bid_updates', 'sms_payments')
    search_fields = ('user__username',)
    raw_id_fields = ('user',)


@admin.register(WebPushSubscription)
class WebPushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'endpoint', 'created_at')
    search_fields = ('user__username', 'endpoint')
    readonly_fields = ('created_at', 'updated_at')
    raw_id_fields = ('user',)
    list_filter = ('created_at',)
