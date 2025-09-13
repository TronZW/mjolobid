from django import forms
from .models import PaymentMethod, WithdrawalRequest


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
