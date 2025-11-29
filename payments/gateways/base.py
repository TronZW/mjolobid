"""
Base payment gateway interface
"""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Dict, Optional
from django.conf import settings


class PaymentGateway(ABC):
    """Base class for all payment gateways"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.gateway_name = self.__class__.__name__
    
    @abstractmethod
    def initiate_payment(self, amount: Decimal, currency: str, reference: str, 
                        customer_phone: str, customer_email: str = '', 
                        description: str = '', **kwargs) -> Dict:
        """
        Initiate a payment request
        
        Returns:
            {
                'success': bool,
                'payment_url': str (optional),
                'payment_reference': str,
                'gateway_response': dict,
                'error': str (if failed)
            }
        """
        pass
    
    @abstractmethod
    def verify_payment(self, payment_reference: str) -> Dict:
        """
        Verify payment status
        
        Returns:
            {
                'success': bool,
                'status': str ('PENDING', 'COMPLETED', 'FAILED'),
                'amount': Decimal,
                'gateway_response': dict,
                'error': str (if failed)
            }
        """
        pass
    
    @abstractmethod
    def handle_webhook(self, request_data: Dict) -> Dict:
        """
        Handle webhook callback from payment gateway
        
        Returns:
            {
                'success': bool,
                'payment_reference': str,
                'status': str,
                'amount': Decimal,
                'gateway_response': dict,
                'error': str (if failed)
            }
        """
        pass
    
    def get_supported_currencies(self) -> list:
        """Get list of supported currencies"""
        return ['USD', 'ZWL']
    
    def get_minimum_amount(self) -> Decimal:
        """Get minimum payment amount"""
        return Decimal('1.00')
    
    def get_maximum_amount(self) -> Decimal:
        """Get maximum payment amount"""
        return Decimal('10000.00')
    
    def format_phone_number(self, phone: str) -> str:
        """Format phone number to standard format"""
        # Remove spaces and dashes
        phone = phone.replace(' ', '').replace('-', '')
        
        # Ensure it starts with country code
        if phone.startswith('0'):
            phone = '+263' + phone[1:]
        elif not phone.startswith('+263') and not phone.startswith('263'):
            phone = '+263' + phone
        
        return phone

