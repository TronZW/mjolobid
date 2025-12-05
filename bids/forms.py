from django import forms
from django.utils import timezone
from django.forms import inlineformset_factory
from .models import Bid, BidMessage, BidReview, EventPromotion, BidPerk


class BidForm(forms.ModelForm):
    """Form for creating/editing bids"""
    
    EVENT_CATEGORY_CHOICES = [
        ('', 'Select a category'),
        ('club_night', '🕺 Club Night'),
        ('concert', '🎵 Concert'),
        ('restaurant', '🍽️ Restaurant'),
        ('movie', '🎬 Movie'),
        ('sports_event', '⚽ Sports Event'),
        ('beach_day', '🏖️ Beach Day'),
        ('shopping', '🛍️ Shopping'),
        ('art_exhibition', '🎨 Art Exhibition'),
        ('hiking', '🥾 Hiking'),
        ('other', '✨ Other'),
    ]
    
    event_category = forms.ChoiceField(
        choices=EVENT_CATEGORY_CHOICES,
        widget=forms.Select(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-200'
        })
    )
    
    custom_category = forms.CharField(
        required=False,
        max_length=100,
        widget=forms.TextInput(attrs={
            'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent transition-all duration-200',
            'placeholder': 'Enter custom category...'
        })
    )
    
    bid_type = forms.ChoiceField(
        choices=[('MONEY', 'Money'), ('PERKS', 'Perks')],
        widget=forms.RadioSelect(attrs={'class': 'form-radio'}),
        initial='MONEY'
    )
    
    class Meta:
        model = Bid
        fields = [
            'title', 'description', 'event_date', 
            'event_location', 'event_address', 'bid_amount', 'bid_type'
        ]
        widgets = {
            'event_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'event_address': forms.Textarea(attrs={'rows': 2}),
            'bid_amount': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '5',
                'max': '500',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['event_date'].input_formats = ['%Y-%m-%dT%H:%M']
        
        # Set bid_type initial value if editing
        if self.instance and self.instance.pk:
            if self.instance.bid_type:
                self.fields['bid_type'].initial = self.instance.bid_type
            # If editing an existing bid, set the category choice
            if self.instance.event_category:
                category_name = self.instance.event_category.name.lower().replace(' ', '_')
                if category_name in [choice[0] for choice in self.EVENT_CATEGORY_CHOICES]:
                    self.fields['event_category'].initial = category_name
                else:
                    self.fields['event_category'].initial = 'other'
                    self.fields['custom_category'].initial = self.instance.event_category.name
        else:
            # New bid - set default bid_type
            self.fields['bid_type'].initial = 'MONEY'
        
        # Make bid_amount conditionally required
        if self.data:
            bid_type = self.data.get('bid_type', 'MONEY')
        elif self.instance and self.instance.pk:
            bid_type = self.instance.bid_type
        else:
            bid_type = self.fields['bid_type'].initial
        
        if bid_type == 'PERKS':
            self.fields['bid_amount'].required = False
        else:
            self.fields['bid_amount'].required = True
    
    def clean_bid_amount(self):
        amount = self.cleaned_data.get('bid_amount')
        
        # Get bid_type from form data (not cleaned_data, as clean() hasn't run yet)
        # Try cleaned_data first (in case clean() already ran), then fall back to data
        bid_type = self.cleaned_data.get('bid_type') or self.data.get('bid_type', 'MONEY')
        
        # Only validate amount for money bids
        # If bid_type is PERKS, skip validation and return None
        if bid_type == 'PERKS':
            return None
        
        if bid_type == 'MONEY':
            if not amount:
                raise forms.ValidationError('Bid amount is required for money bids.')
            from django.conf import settings
            min_amount = settings.MJOLOBID_SETTINGS['MIN_BID_AMOUNT']
            max_amount = settings.MJOLOBID_SETTINGS['MAX_BID_AMOUNT']
            
            if amount < min_amount:
                raise forms.ValidationError(f'Minimum bid amount is ${min_amount}')
            if amount > max_amount:
                raise forms.ValidationError(f'Maximum bid amount is ${max_amount}')
        
        return amount
    
    def clean_event_date(self):
        event_date = self.cleaned_data.get('event_date')
        if event_date:
            # Allow same-day bids - check if event date is at least today (not in the past)
            now = timezone.now()
            # Compare dates (not datetime) - allow same day
            event_date_only = event_date.date()
            today = now.date()
            
            if event_date_only < today:
                raise forms.ValidationError('Event date cannot be in the past')
            # If same day, check that the time is not in the past
            elif event_date_only == today and event_date.time() < now.time():
                raise forms.ValidationError('Event time cannot be in the past')
        return event_date
    
    def clean(self):
        cleaned_data = super().clean()
        event_category = cleaned_data.get('event_category')
        custom_category = cleaned_data.get('custom_category')
        bid_type = cleaned_data.get('bid_type', 'MONEY')
        bid_amount = cleaned_data.get('bid_amount')
        
        # If "Other" is selected, custom_category is required
        if event_category == 'other' and not custom_category:
            self.add_error('custom_category', 'Please specify the custom category.')
        
        # Validate bid_type requirements
        if bid_type == 'MONEY':
            if not bid_amount:
                self.add_error('bid_amount', 'Bid amount is required for money bids.')
        elif bid_type == 'PERKS':
            # Clear bid_amount if perks is selected (ensure it's None)
            cleaned_data['bid_amount'] = None
            # Remove any bid_amount errors since it's not required for perks
            if 'bid_amount' in self.errors:
                del self.errors['bid_amount']
        
        return cleaned_data


class BidMessageForm(forms.ModelForm):
    """Form for sending messages"""
    
    class Meta:
        model = BidMessage
        fields = ['message']
        widgets = {
            'message': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Type your message here...'})
        }


class BidReviewForm(forms.ModelForm):
    """Form for reviewing bids"""
    
    class Meta:
        model = BidReview
        fields = ['rating', 'review_text']
        widgets = {
            'review_text': forms.Textarea(attrs={'rows': 3, 'placeholder': 'Write your review here...'})
        }


class BidPerkForm(forms.ModelForm):
    """Form for individual perk items"""
    
    class Meta:
        model = BidPerk
        fields = ['category', 'description', 'estimated_value', 'quantity']
        widgets = {
            'category': forms.Select(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'description': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': 'e.g., 2 VIP tickets to Taylor Swift concert',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'estimated_value': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'placeholder': 'Optional',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'quantity': forms.NumberInput(attrs={
                'min': '1',
                'value': '1',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
        }
    
    def clean_estimated_value(self):
        value = self.cleaned_data.get('estimated_value')
        # Optional field, but if provided, must be positive
        if value is not None and value < 0:
            raise forms.ValidationError('Estimated value cannot be negative.')
        return value


# Formset for multiple perks (min_num=0 for new bids, will validate in view)
BidPerkFormSet = inlineformset_factory(
    Bid, 
    BidPerk, 
    form=BidPerkForm,
    extra=1,
    can_delete=True,
    min_num=0,  # Will validate in view for PERKS type
    validate_min=False,
    max_num=10  # Limit to 10 perks per bid
)


class EventPromotionForm(forms.ModelForm):
    """Form for creating/editing event promotions"""
    
    class Meta:
        model = EventPromotion
        fields = [
            'title', 'description', 'event_date', 'location', 
            'image', 'link_url', 'priority', 'end_date', 'cost'
        ]
        widgets = {
            'event_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'priority': forms.NumberInput(attrs={'min': 0, 'max': 100}),
            'cost': forms.NumberInput(attrs={'step': '0.01', 'min': '0'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['event_date'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['end_date'].input_formats = ['%Y-%m-%dT%H:%M']
    
    def clean_event_date(self):
        event_date = self.cleaned_data.get('event_date')
        if event_date:
            # Allow same-day events - check if event date is at least today (not in the past)
            now = timezone.now()
            # Compare dates (not datetime) - allow same day
            event_date_only = event_date.date()
            today = now.date()
            
            if event_date_only < today:
                raise forms.ValidationError('Event date cannot be in the past')
            # If same day, check that the time is not in the past
            elif event_date_only == today and event_date.time() < now.time():
                raise forms.ValidationError('Event time cannot be in the past')
        return event_date
    
    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')
        event_date = self.cleaned_data.get('event_date')
        if end_date and event_date and end_date <= event_date:
            raise forms.ValidationError('End date must be after event date')
        return end_date
