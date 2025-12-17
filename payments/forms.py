from django import forms
from .models import PaymentMethod, WithdrawalRequest, ManualPayment


class PaymentMethodForm(forms.ModelForm):
    """Form for adding payment methods"""
    
    class Meta:
        model = PaymentMethod
        fields = ['payment_type', 'account_number', 'account_name']
        widgets = {
            'payment_type': forms.Select(attrs={'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary'}),
            'account_number': forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary', 'placeholder': 'Phone number or account number'}),
            'account_name': forms.TextInput(attrs={'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary', 'placeholder': 'Account holder name'}),
        }
    
    def clean_account_number(self):
        account_number = self.cleaned_data.get('account_number')
        payment_type = self.cleaned_data.get('payment_type')
        
        if payment_type in ['ECOCASH', 'ONEMONEY', 'INNBUCKS']:
            # Validate phone number format
            if not account_number.startswith('+263') and not account_number.startswith('263'):
                raise forms.ValidationError('Please enter a valid Zimbabwean phone number starting with +263 or 263')
        
        return account_number


class WithdrawalRequestForm(forms.ModelForm):
    """Form for withdrawal requests"""
    
    class Meta:
        model = WithdrawalRequest
        fields = ['amount', 'payment_method']
        widgets = {
            'amount': forms.NumberInput(attrs={'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary', 'step': '0.01', 'min': '10.00'}),
            'payment_method': forms.Select(attrs={'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary'}),
        }
    
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount and amount < 10.00:
            raise forms.ValidationError('Minimum withdrawal amount is $10.00')
        return amount


class ManualPaymentForm(forms.ModelForm):
    """Form for submitting manual payment proof"""
    
    class Meta:
        model = ManualPayment
        fields = ['sender_name', 'ecocash_reference', 'sender_phone']
        widgets = {
            'sender_name': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary',
                'placeholder': 'Enter your full name'
            }),
            'ecocash_reference': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary',
                'placeholder': 'Enter EcoCash TXN ID (e.g., TXN123456789)'
            }),
            'sender_phone': forms.TextInput(attrs={
                'class': 'w-full border border-gray-300 rounded-lg px-3 py-2 focus:outline-none focus:ring-2 focus:ring-primary',
                'placeholder': 'Your EcoCash number (optional)'
            }),
        }
        labels = {
            'sender_name': 'Your Name',
            'ecocash_reference': 'EcoCash Transaction ID (TXN ID)',
            'sender_phone': 'Your Phone Number (Optional)',
        }
    
    def clean_ecocash_reference(self):
        reference = self.cleaned_data.get('ecocash_reference')
        if not reference:
            raise forms.ValidationError('EcoCash transaction reference is required')
        # Remove spaces and convert to uppercase
        reference = reference.strip().upper()
        if len(reference) < 5:
            raise forms.ValidationError('Please enter a valid EcoCash transaction reference')
        return reference
    
    def clean_sender_name(self):
        name = self.cleaned_data.get('sender_name')
        if not name or len(name.strip()) < 2:
            raise forms.ValidationError('Please enter your full name')
        return name.strip()
