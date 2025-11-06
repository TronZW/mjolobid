from django.db import models
from django.utils import timezone
from accounts.models import User
from bids.models import EventCategory
from decimal import Decimal


class Offer(models.Model):
    """Offer model - Girls create offers for events or specific days"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('ACCEPTED', 'Accepted'),
        ('COMPLETED', 'Completed'),
        ('CANCELLED', 'Cancelled'),
        ('EXPIRED', 'Expired'),
    ]
    
    # Basic offer information
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='offers_posted')
    title = models.CharField(max_length=200)
    description = models.TextField(max_length=500)
    event_category = models.ForeignKey(EventCategory, on_delete=models.CASCADE, null=True, blank=True)
    
    # Event/Date details
    event_date = models.DateTimeField(null=True, blank=True, help_text="Specific event date (optional)")
    available_date = models.DateField(null=True, blank=True, help_text="General availability date (optional)")
    event_location = models.CharField(max_length=200, blank=True)
    event_address = models.TextField(blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Financial details
    minimum_bid = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, help_text="Minimum bid amount")
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Status and matching
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    accepted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='offers_accepted')
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    # Premium features
    is_boosted = models.BooleanField(default=False)
    is_highlighted = models.BooleanField(default=False)
    boost_expires = models.DateTimeField(null=True, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.title} by {self.user.username}"
    
    def save(self, *args, **kwargs):
        from django.conf import settings
        if not self.commission_amount and self.minimum_bid:
            commission_rate = settings.MJOLOBID_SETTINGS['COMMISSION_RATE']
            self.commission_amount = self.minimum_bid * Decimal(str(commission_rate))
        
        # Set expiration date if not set
        if not self.expires_at:
            if self.event_date:
                self.expires_at = self.event_date - timezone.timedelta(hours=2)
            elif self.available_date:
                from datetime import datetime
                self.expires_at = datetime.combine(
                    self.available_date, 
                    datetime.max.time()
                ).replace(tzinfo=timezone.get_current_timezone()) - timezone.timedelta(hours=2)
        
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        if self.expires_at:
            return timezone.now() > self.expires_at
        return False
    
    @property
    def time_until_event(self):
        from datetime import datetime
        target_date = self.event_date or (datetime.combine(
            self.available_date, 
            datetime.max.time()
        ).replace(tzinfo=timezone.get_current_timezone()) if self.available_date else None)
        
        if target_date and target_date > timezone.now():
            delta = target_date - timezone.now()
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
    def bid_count(self):
        """Get total number of bids on this offer"""
        return self.bids.count()
    
    @property
    def highest_bid(self):
        """Get the highest bid amount"""
        from django.db.models import Max
        highest = self.bids.aggregate(Max('bid_amount'))['bid_amount__max']
        return highest if highest else self.minimum_bid


class OfferBid(models.Model):
    """Bids placed on offers by men"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('SELECTED', 'Selected'),
        ('REJECTED', 'Rejected'),
        ('WITHDRAWN', 'Withdrawn'),
    ]
    
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='bids')
    bidder = models.ForeignKey(User, on_delete=models.CASCADE, related_name='offer_bids')
    bid_amount = models.DecimalField(max_digits=10, decimal_places=2)
    message = models.TextField(max_length=500, blank=True, help_text="Optional message to the offer creator")
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-bid_amount', '-created_at']
        unique_together = ('offer', 'bidder')
    
    def __str__(self):
        return f"${self.bid_amount} bid on {self.offer.title} by {self.bidder.username}"
    
    def clean(self):
        # Validation is handled in the form, not here
        # This method is kept for potential future use but doesn't validate
        pass


class OfferView(models.Model):
    """Track when users view offers"""
    
    offer = models.ForeignKey(Offer, on_delete=models.CASCADE, related_name='views')
    viewer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='offer_views')
    viewed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ('offer', 'viewer')
        verbose_name = 'Offer View'
        verbose_name_plural = 'Offer Views'
    
    def __str__(self):
        return f"{self.viewer.username} viewed {self.offer.title}"
