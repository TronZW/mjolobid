from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserProfile, UserRating, EmailVerification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin"""
    
    list_display = ('username', 'email', 'user_type', 'gender', 'city', 'is_verified', 'is_premium', 'created_at')
    list_filter = ('user_type', 'gender', 'is_verified', 'is_premium', 'city', 'created_at')
    search_fields = ('username', 'email', 'phone_number', 'city')
    ordering = ('-created_at',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Profile Information', {
            'fields': ('gender', 'user_type', 'date_of_birth', 'phone_number', 'profile_picture', 'bio')
        }),
        ('Location', {
            'fields': ('city', 'location', 'latitude', 'longitude')
        }),
        ('Account Status', {
            'fields': ('is_verified', 'is_premium', 'premium_expires')
        }),
        ('Financial', {
            'fields': ('wallet_balance', 'total_earned', 'total_spent')
        }),
        ('Subscription', {
            'fields': ('subscription_active', 'subscription_expires')
        }),
        ('Affiliate', {
            'fields': ('referral_code', 'referred_by', 'total_referrals', 'referral_earnings')
        }),
        ('Activity', {
            'fields': ('last_seen',)
        }),
    )


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    """User Profile admin"""
    
    list_display = ('user', 'occupation', 'average_rating', 'total_reviews', 'id_verified')
    list_filter = ('id_verified', 'phone_verified', 'email_verified')
    search_fields = ('user__username', 'user__email', 'occupation')
    raw_id_fields = ('user',)


@admin.register(UserRating)
class UserRatingAdmin(admin.ModelAdmin):
    """User Rating admin"""
    
    list_display = ('rated_user', 'rating_user', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('rated_user__username', 'rating_user__username')
    raw_id_fields = ('rated_user', 'rating_user')


@admin.register(EmailVerification)
class EmailVerificationAdmin(admin.ModelAdmin):
    """Email Verification admin"""
    
    list_display = ('email', 'code', 'verification_type', 'is_used', 'is_expired', 'created_at', 'expires_at')
    list_filter = ('verification_type', 'is_used', 'created_at')
    search_fields = ('email', 'code')
    readonly_fields = ('created_at', 'expires_at', 'is_expired')
    raw_id_fields = ('user',)
    
    def is_expired(self, obj):
        return obj.is_expired()
    is_expired.boolean = True
    is_expired.short_description = 'Expired'
