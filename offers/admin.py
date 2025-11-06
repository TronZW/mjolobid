from django.contrib import admin
from .models import Offer, OfferBid, OfferView


@admin.register(Offer)
class OfferAdmin(admin.ModelAdmin):
    """Admin for Offer model"""
    
    list_display = ('title', 'user', 'status', 'minimum_bid', 'event_date', 'available_date', 'created_at')
    list_filter = ('status', 'event_category', 'created_at', 'is_boosted')
    search_fields = ('title', 'description', 'user__username', 'event_location')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('user', 'title', 'description', 'event_category')
        }),
        ('Date & Location', {
            'fields': ('event_date', 'available_date', 'event_location', 'event_address', 'latitude', 'longitude')
        }),
        ('Financial', {
            'fields': ('minimum_bid', 'commission_amount')
        }),
        ('Status', {
            'fields': ('status', 'accepted_by', 'accepted_at')
        }),
        ('Premium', {
            'fields': ('is_boosted', 'is_highlighted', 'boost_expires')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'expires_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'commission_amount')


@admin.register(OfferBid)
class OfferBidAdmin(admin.ModelAdmin):
    """Admin for OfferBid model"""
    
    list_display = ('offer', 'bidder', 'bid_amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('offer__title', 'bidder__username')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Bid Information', {
            'fields': ('offer', 'bidder', 'bid_amount', 'message')
        }),
        ('Status', {
            'fields': ('status',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at')


@admin.register(OfferView)
class OfferViewAdmin(admin.ModelAdmin):
    """Admin for OfferView model"""
    
    list_display = ('offer', 'viewer', 'viewed_at')
    list_filter = ('viewed_at',)
    search_fields = ('offer__title', 'viewer__username')
    ordering = ('-viewed_at',)
