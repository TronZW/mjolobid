from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
from django.conf import settings


class User(AbstractUser):
    """Custom User model for MjoloBid"""
    
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    
    USER_TYPE_CHOICES = [
        ('M', 'Male User'),
        ('F', 'Female User'),
    ]
    
    # Basic profile information
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    user_type = models.CharField(max_length=1, choices=USER_TYPE_CHOICES)
    date_of_birth = models.DateField(null=True, blank=True)
    phone_number = models.CharField(max_length=15, unique=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', null=True, blank=True)
    bio = models.TextField(max_length=500, blank=True)
    
    # Location information
    city = models.CharField(max_length=100, default='Harare')
    location = models.CharField(max_length=200, blank=True)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Account status and verification
    is_verified = models.BooleanField(default=False)
    is_premium = models.BooleanField(default=False)
    premium_expires = models.DateTimeField(null=True, blank=True)
    
    # Financial information
    wallet_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_earned = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_spent = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Subscription information
    subscription_active = models.BooleanField(default=False)
    subscription_expires = models.DateTimeField(null=True, blank=True)
    
    # Affiliate information
    referral_code = models.CharField(max_length=10, unique=True, null=True, blank=True)
    referred_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='referrals')
    total_referrals = models.IntegerField(default=0)
    referral_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    last_seen = models.DateTimeField(default=timezone.now)
    
    def __str__(self):
        return f"{self.username} ({self.get_user_type_display()})"
    
    def save(self, *args, **kwargs):
        if not self.referral_code:
            import random
            import string
            self.referral_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        super().save(*args, **kwargs)
    
    def get_profile_picture_url(self) -> str:
        """Return a usable URL for the user's profile picture.

        Handles both local FileSystemStorage paths and legacy absolute URLs
        that may have been stored when using a remote storage backend.
        """
        if not self.profile_picture:
            return ""

        # Try the storage-provided URL first
        try:
            url = self.profile_picture.url
            if isinstance(url, str) and (url.startswith('http://') or url.startswith('https://') or url.startswith('/')):
                return url
        except Exception:
            # Fall back to interpreting the stored value directly
            name = str(self.profile_picture)
            if name.startswith('http://') or name.startswith('https://'):
                return name
            # Build a local media URL
            base = getattr(settings, 'MEDIA_URL', '/media/')
            if not base.endswith('/'):
                base += '/'
            return f"{base}{name}"

        return url

    @property
    def age(self):
        if self.date_of_birth:
            today = timezone.now().date()
            return today.year - self.date_of_birth.year - ((today.month, today.day) < (self.date_of_birth.month, self.date_of_birth.day))
        return None
    
    @property
    def is_online(self):
        """Check if user was active in the last 5 minutes"""
        if self.last_seen:
            return (timezone.now() - self.last_seen).total_seconds() < 300
        return False
    
    def get_whatsapp_number(self):
        """Format phone number for WhatsApp links (removes +, spaces, and converts 0 to 263)"""
        if not self.phone_number:
            return None
        # Remove +, spaces, dashes, and parentheses
        number = ''.join(c for c in self.phone_number if c.isdigit())
        # If starts with 0, replace with 263 (Zimbabwe country code)
        if number.startswith('0') and len(number) > 1:
            number = '263' + number[1:]
        # If starts with +263, remove the +
        elif number.startswith('263'):
            pass  # Already correct
        return number


class UserProfile(models.Model):
    """Extended profile information"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Additional profile information
    occupation = models.CharField(max_length=100, blank=True)
    education = models.CharField(max_length=100, blank=True)
    interests = models.TextField(blank=True)
    
    # Social media links
    instagram = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    
    # Preferences
    preferred_events = models.JSONField(default=list, blank=True)
    max_distance = models.IntegerField(default=10)  # in kilometers
    
    # Safety and verification
    id_verified = models.BooleanField(default=False)
    phone_verified = models.BooleanField(default=False)
    email_verified = models.BooleanField(default=False)
    
    # Rating and reviews
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_reviews = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Profile"


class UserRating(models.Model):
    """User ratings and reviews"""
    
    RATING_CHOICES = [
        (1, '1 Star'),
        (2, '2 Stars'),
        (3, '3 Stars'),
        (4, '4 Stars'),
        (5, '5 Stars'),
    ]
    
    rated_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_received')
    rating_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ratings_given')
    rating = models.IntegerField(choices=RATING_CHOICES)
    review = models.TextField(max_length=500, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['rated_user', 'rating_user']
    
    def __str__(self):
        return f"{self.rating_user.username} rated {self.rated_user.username} {self.rating} stars"


class UserGallery(models.Model):
    """User gallery images for profile showcase"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='gallery_images')
    image = models.ImageField(upload_to='gallery/')
    caption = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False, help_text="Primary image for profile")
    uploaded_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_primary', '-uploaded_at']
        verbose_name_plural = "User Gallery Images"
    
    def __str__(self):
        return f"{self.user.username}'s gallery image - {self.caption or 'No caption'}"
    
    def save(self, *args, **kwargs):
        # If this is set as primary, unset other primary images for this user
        if self.is_primary:
            UserGallery.objects.filter(user=self.user, is_primary=True).exclude(id=self.id).update(is_primary=False)
        super().save(*args, **kwargs)
    
    def get_image_url(self):
        """Return a usable URL for the image"""
        if not self.image:
            return ""
        
        try:
            url = self.image.url
            if isinstance(url, str) and (url.startswith('http://') or url.startswith('https://') or url.startswith('/')):
                return url
        except Exception:
            # Fall back to interpreting the stored value directly
            name = str(self.image)
            if name.startswith('http://') or name.startswith('https://'):
                return name
            # Build a local media URL
            from django.conf import settings
            base = getattr(settings, 'MEDIA_URL', '/media/')
            if not base.endswith('/'):
                base += '/'
            return f"{base}{name}"
        
        return url


class EmailVerification(models.Model):
    """Model to store email verification codes"""
    
    VERIFICATION_TYPES = [
        ('REGISTRATION', 'Registration'),
        ('PASSWORD_RESET', 'Password Reset'),
    ]
    
    email = models.EmailField()
    code = models.CharField(max_length=6)
    verification_type = models.CharField(max_length=20, choices=VERIFICATION_TYPES)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name='email_verifications')
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['email', 'code', 'verification_type']),
        ]
    
    def __str__(self):
        return f"{self.email} - {self.code} ({self.verification_type})"
    
    def is_expired(self):
        """Check if verification code has expired"""
        from django.utils import timezone
        return timezone.now() > self.expires_at
    
    def is_valid(self):
        """Check if verification code is valid (not used and not expired)"""
        return not self.is_used and not self.is_expired()
    
    def mark_as_used(self):
        """Mark verification code as used"""
        self.is_used = True
        self.save(update_fields=['is_used'])