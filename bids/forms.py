from django import forms
from django.utils import timezone
from .models import Bid, BidMessage, BidReview, EventPromotion


class BidForm(forms.ModelForm):
    """Form for creating/editing bids"""
    
    class Meta:
        model = Bid
        fields = [
            'title', 'description', 'event_category', 'event_date', 
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
