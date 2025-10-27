from django import forms
from django.utils import timezone
from .models import Bid, BidMessage, BidReview, EventPromotion


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
    
    class Meta:
        model = Bid
        fields = [
            'title', 'description', 'event_date', 
            'event_location', 'event_address', 'bid_amount'
        ]
        widgets = {
            'event_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'event_address': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['event_date'].input_formats = ['%Y-%m-%dT%H:%M']
        
        # If editing an existing bid, set the category choice
        if self.instance and self.instance.pk:
            if self.instance.event_category:
                category_name = self.instance.event_category.name.lower().replace(' ', '_')
                if category_name in [choice[0] for choice in self.EVENT_CATEGORY_CHOICES]:
                    self.fields['event_category'].initial = category_name
                else:
                    self.fields['event_category'].initial = 'other'
                    self.fields['custom_category'].initial = self.instance.event_category.name
    
    def clean_bid_amount(self):
        amount = self.cleaned_data.get('bid_amount')
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
        if event_date and event_date <= timezone.now():
            raise forms.ValidationError('Event date must be in the future')
        return event_date
    
    def clean(self):
        cleaned_data = super().clean()
        event_category = cleaned_data.get('event_category')
        custom_category = cleaned_data.get('custom_category')
        
        # If "Other" is selected, custom_category is required
        if event_category == 'other' and not custom_category:
            self.add_error('custom_category', 'Please specify the custom category.')
        
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
        if event_date and event_date <= timezone.now():
            raise forms.ValidationError('Event date must be in the future')
        return event_date
    
    def clean_end_date(self):
        end_date = self.cleaned_data.get('end_date')
        event_date = self.cleaned_data.get('event_date')
        if end_date and event_date and end_date <= event_date:
            raise forms.ValidationError('End date must be after event date')
        return end_date
