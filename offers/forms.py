from django import forms
from django.utils import timezone
from .models import Offer, OfferBid


class OfferForm(forms.ModelForm):
    """Form for creating/editing offers"""
    
    EVENT_CATEGORY_CHOICES = [
        ('', 'Select a category (optional)'),
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
        required=False,
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
    
    class Meta:
        model = Offer
        fields = [
            'title', 'description', 'event_date', 'available_date',
            'event_location', 'event_address', 'minimum_bid'
        ]
        widgets = {
            'event_date': forms.DateTimeInput(attrs={
                'type': 'datetime-local',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'available_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'description': forms.Textarea(attrs={
                'rows': 4,
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'event_address': forms.Textarea(attrs={
                'rows': 2,
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'title': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'event_location': forms.TextInput(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'minimum_bid': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['event_date'].input_formats = ['%Y-%m-%dT%H:%M']
        self.fields['available_date'].input_formats = ['%Y-%m-%d']
        
        # If editing an existing offer, set the category choice
        if self.instance and self.instance.pk:
            if self.instance.event_category:
                category_name = self.instance.event_category.name.lower().replace(' ', '_')
                if category_name in [choice[0] for choice in self.EVENT_CATEGORY_CHOICES]:
                    self.fields['event_category'].initial = category_name
                else:
                    self.fields['event_category'].initial = 'other'
                    self.fields['custom_category'].initial = self.instance.event_category.name
    
    def clean_minimum_bid(self):
        amount = self.cleaned_data.get('minimum_bid')
        from django.conf import settings
        min_amount = settings.MJOLOBID_SETTINGS['MIN_BID_AMOUNT']
        max_amount = settings.MJOLOBID_SETTINGS['MAX_BID_AMOUNT']
        
        if amount and amount < min_amount:
            raise forms.ValidationError(f'Minimum bid amount is ${min_amount}')
        if amount and amount > max_amount:
            raise forms.ValidationError(f'Maximum bid amount is ${max_amount}')
        
        return amount
    
    def clean_event_date(self):
        event_date = self.cleaned_data.get('event_date')
        if event_date and event_date <= timezone.now():
            raise forms.ValidationError('Event date must be in the future')
        return event_date
    
    def clean_available_date(self):
        available_date = self.cleaned_data.get('available_date')
        if available_date and available_date < timezone.now().date():
            raise forms.ValidationError('Available date must be today or in the future')
        return available_date
    
    def clean(self):
        cleaned_data = super().clean()
        event_category = cleaned_data.get('event_category')
        custom_category = cleaned_data.get('custom_category')
        event_date = cleaned_data.get('event_date')
        available_date = cleaned_data.get('available_date')
        
        # At least one date must be provided
        if not event_date and not available_date:
            raise forms.ValidationError('Please provide either an event date or available date.')
        
        # If "Other" is selected, custom_category is required
        if event_category == 'other' and not custom_category:
            self.add_error('custom_category', 'Please specify the custom category.')
        
        return cleaned_data


class OfferBidForm(forms.ModelForm):
    """Form for placing a bid on an offer"""
    
    class Meta:
        model = OfferBid
        fields = ['bid_amount', 'message']
        widgets = {
            'bid_amount': forms.NumberInput(attrs={
                'step': '0.01',
                'min': '0',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
            'message': forms.Textarea(attrs={
                'rows': 3,
                'placeholder': 'Optional message to the offer creator...',
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-xl focus:ring-2 focus:ring-primary focus:border-transparent'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        self.offer = kwargs.pop('offer', None)
        super().__init__(*args, **kwargs)
        
        if self.offer:
            self.fields['bid_amount'].widget.attrs['min'] = float(self.offer.minimum_bid)
            self.fields['bid_amount'].help_text = f'Minimum bid: ${self.offer.minimum_bid}'
    
    def clean_bid_amount(self):
        amount = self.cleaned_data.get('bid_amount')
        
        if self.offer and amount:
            if amount < self.offer.minimum_bid:
                raise forms.ValidationError(
                    f'Bid amount must be at least ${self.offer.minimum_bid}'
                )
            
            from django.conf import settings
            max_amount = settings.MJOLOBID_SETTINGS['MAX_BID_AMOUNT']
            if amount > max_amount:
                raise forms.ValidationError(
                    f'Maximum bid amount is ${max_amount}'
                )
        
        return amount

