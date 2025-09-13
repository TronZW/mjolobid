from django.contrib import admin
from .models import EventCategory, Bid, BidImage, BidMessage, BidReview, EventPromotion


@admin.register(EventCategory)
class EventCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'icon', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'bid_amount', 'status', 'event_date', 'created_at')
    list_filter = ('status', 'event_category', 'is_boosted', 'created_at')
    search_fields = ('title', 'user__username', 'event_location')
    raw_id_fields = ('user', 'accepted_by')
    readonly_fields = ('created_at', 'updated_at', 'commission_amount')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'description', 'event_category')
        }),
        ('Event Details', {
            'fields': ('event_date', 'event_location', 'event_address', 'latitude', 'longitude')
        }),
        ('Financial', {
            'fields': ('bid_amount', 'commission_amount')
        }),
        ('Status', {
            'fields': ('status', 'accepted_by', 'accepted_at')
        }),
        ('Premium Features', {
            'fields': ('is_boosted', 'is_highlighted', 'boost_expires')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'expires_at')
        }),
    )


@admin.register(BidImage)
class BidImageAdmin(admin.ModelAdmin):
    list_display = ('bid', 'is_primary', 'created_at')
    list_filter = ('is_primary', 'created_at')
    raw_id_fields = ('bid',)


@admin.register(BidMessage)
class BidMessageAdmin(admin.ModelAdmin):
    list_display = ('bid', 'sender', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('message', 'sender__username')
    raw_id_fields = ('bid', 'sender')


@admin.register(BidReview)
class BidReviewAdmin(admin.ModelAdmin):
    list_display = ('bid', 'reviewer', 'reviewed_user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('review_text', 'reviewer__username', 'reviewed_user__username')
    raw_id_fields = ('bid', 'reviewer', 'reviewed_user')


@admin.register(EventPromotion)
class EventPromotionAdmin(admin.ModelAdmin):
    list_display = ('title', 'event_date', 'location', 'is_active', 'priority', 'cost', 'clicks')
    list_filter = ('is_active', 'priority', 'created_at')
    search_fields = ('title', 'location')
    readonly_fields = ('clicks', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Event Information', {
            'fields': ('title', 'description', 'event_date', 'location', 'image', 'link_url')
        }),
        ('Promotion Settings', {
            'fields': ('is_active', 'priority', 'start_date', 'end_date')
        }),
        ('Financial', {
            'fields': ('cost', 'clicks')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
