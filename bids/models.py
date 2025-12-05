from django.db import models
from django.utils import timezone
from accounts.models import User
from decimal import Decimal


class EventCategory(models.Model):
    """Event categories"""
    
    name = models.CharField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, default='🎉')  # Emoji icon
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return self.name


class Bid(models.Model):
    """Bid model for social events"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
    ]
    
    # Basic bid information
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bids_posted')
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=500)
    event_category = models.ForeignKey(EventCategory, on_delete=models.CASCADE)
    
    # Event details
    event_date = models.DateTimeField()
    event_location = models.CharField(max_length=200)
    event_address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Bid type and financial details
    BID_TYPE_CHOICES = [
        ('MONEY', 'Money'),
        ('PERKS', 'Perks'),
    ]
    bid_type = models.CharField(max_length=20, choices=BID_TYPE_CHOICES, default='MONEY')
    bid_amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    total_perk_value = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Sum of estimated values for all perks")
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Status and matching
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    accepted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='bids_accepted')
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    # Premium features
    is_boosted = models.BooleanField(default=False)
    is_highlighted = models.BooleanField(default=False)
    boost_expires = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        if self.bid_type == 'MONEY' and self.bid_amount:
            return f"{self.title} - ${self.bid_amount} by {self.user.username}"
        elif self.bid_type == 'PERKS':
            perk_count = self.perks.count()
            return f"{self.title} - {perk_count} perk(s) by {self.user.username}"
        return f"{self.title} by {self.user.username}"
    
    def save(self, *args, **kwargs):
        # Calculate commission only for money bids
        if self.bid_type == 'MONEY' and self.bid_amount and not self.commission_amount:
            from django.conf import settings
            commission_rate = settings.MJOLOBID_SETTINGS['COMMISSION_RATE']
            self.commission_amount = self.bid_amount * Decimal(str(commission_rate))
        elif self.bid_type == 'PERKS':
            # No commission on perks (Phase 1)
            self.commission_amount = Decimal('0.00')
            # Calculate total perk value if perks exist
            if self.pk:
                from django.db.models import Sum
                total = self.perks.aggregate(
                    total=Sum('estimated_value')
                )['total'] or Decimal('0.00')
                self.total_perk_value = total
        
        if not self.expires_at:
            self.expires_at = self.event_date - timezone.timedelta(hours=2)
        
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        return timezone.now() > self.expires_at
    
    @property
    def time_until_event(self):
        if self.event_date > timezone.now():
            delta = self.event_date - timezone.now()
            return delta
        return None
    
    @property
    def distance_from_user(self, user_lat, user_lng):
        """Calculate distance from user location"""
        if not self.latitude or not self.longitude or not user_lat or not user_lng:
            return None
        
        from math import radians, cos, sin, asin, sqrt
        
        # Haversine formula
        lat1, lon1 = radians(float(user_lat)), radians(float(user_lng))
        lat2, lon2 = radians(float(self.latitude)), radians(float(self.longitude))
        
        dlat = lat2 - lat1
        dlon = lon2 - lon1
        a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
        c = 2 * asin(sqrt(a))
        r = 6371  # Earth's radius in kilometers
        
        return round(c * r, 1)
    
    @property
    def pending_acceptances(self):
        """Get all pending acceptances for this bid"""
        return self.acceptances.filter(status='PENDING')
    
    @property
    def selected_acceptance(self):
        """Get the selected acceptance for this bid"""
        return self.acceptances.filter(status='SELECTED').first()
    
    @property
    def has_pending_acceptances(self):
        """Check if bid has pending acceptances"""
        return self.pending_acceptances.exists()
    
    @property
    def acceptance_count(self):
        """Get total number of acceptances"""
        return self.acceptances.count()
    
    @property
    def has_perks(self):
        """Check if bid has perks"""
        return self.bid_type == 'PERKS' and self.perks.exists()
    
    @property
    def display_value(self):
        """Get display value for bid (money or total perk value)"""
        if self.bid_type == 'MONEY' and self.bid_amount:
            return f"${self.bid_amount}"
        elif self.bid_type == 'PERKS' and self.total_perk_value:
            return f"${self.total_perk_value} (Perks)"
        elif self.bid_type == 'PERKS':
            return "Perks"
        return "N/A"


class BidImage(models.Model):
    """Images for bids"""
    
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='bid_images/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Image for {self.bid.title}"


class BidMessage(models.Model):
    """Messages between bid poster and acceptor"""
    
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField(max_length=1000)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"Message from {self.sender.username} for {self.bid.title}"


class BidReview(models.Model):
    """Reviews after bid completion"""
    
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE, related_name='reviews')
    reviewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_given')
    reviewed_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reviews_received')
    rating = models.IntegerField(choices=RATING_CHOICES)
    review_text = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['bid', 'reviewer']
    
    def __str__(self):
        return f"Review for {self.bid.title} by {self.reviewer.username}"


class BidView(models.Model):
    """Track when users view bids"""
    
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE, related_name='views')
    viewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bid_views')
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('bid', 'viewer')
        verbose_name = 'Bid View'
        verbose_name_plural = 'Bid Views'
    
    def __str__(self):
        return f"{self.viewer.username} viewed {self.bid.title}"


class BidAcceptance(models.Model):
    """Track multiple acceptances for a bid"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),  # Girl accepted, waiting for male to choose
        ('SELECTED', 'Selected'),  # Male chose this girl
        ('REJECTED', 'Rejected'),  # Male chose someone else
        ('WITHDRAWN', 'Withdrawn'),  # Girl withdrew her acceptance
    ]
    
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE, related_name='acceptances')
    accepted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bid_acceptances')
    accepted_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    message = models.TextField(max_length=500, blank=True)  # Optional message from girl
    
    class Meta:
        unique_together = ('bid', 'accepted_by')
        ordering = ['-accepted_at']
        verbose_name = 'Bid Acceptance'
        verbose_name_plural = 'Bid Acceptances'
    
    def __str__(self):
        return f"{self.accepted_by.username} accepted {self.bid.title} ({self.status})"


class EventPromotion(models.Model):
    """Event promotions for the floating ticker"""
    
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=500)
    event_date = models.DateTimeField()
    location = models.CharField(max_length=200)
    image = models.ImageField(upload_to='event_promotions/', null=True, blank=True)
    link_url = models.URLField(blank=True)
    
    # Promotion settings
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0)  # Higher number = higher priority
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    
    # Financial
    cost = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    clicks = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-priority', '-created_at']
    
    def __str__(self):
        return self.title
    
    @property
    def is_live(self):
        now = timezone.now()
        return self.is_active and self.start_date <= now <= self.end_date


class BidPerk(models.Model):
    """Perks offered instead of money in bids"""
    
    PERK_CATEGORIES = [
        ('CONCERT_TICKETS', '🎵 Concert Tickets'),
        ('ALCOHOL', '🍷 Alcohol/Beverages'),
        ('DINING', '🍽️ Lunch/Dinner'),
        ('FUEL', '⛽ Fuel Coupons'),
        ('TRANSPORT', '🚗 Transportation'),
        ('SHOPPING', '🛍️ Shopping Vouchers'),
        ('ENTERTAINMENT', '🎬 Entertainment'),
        ('OTHER', '✨ Other'),
    ]
    
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE, related_name='perks')
    category = models.CharField(max_length=50, choices=PERK_CATEGORIES)
    description = models.TextField(max_length=200, help_text="e.g., '2 VIP tickets to Taylor Swift concert'")
    estimated_value = models.DecimalField(
        max_digits=10, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text="Optional estimated value in USD for sorting/filtering"
    )
    quantity = models.IntegerField(default=1, help_text="Number of items (e.g., 2 tickets)")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['category', 'created_at']
        verbose_name = 'Bid Perk'
        verbose_name_plural = 'Bid Perks'
    
    def __str__(self):
        return f"{self.get_category_display()} - {self.description[:50]}"
    
    @property
    def display_name(self):
        """Get display name with icon"""
        return f"{self.get_category_display()} - {self.description}"
