"""
Pesepay Payment Gateway Integration
Pesepay supports EcoCash, VISA, and other payment methods
"""
import requests
import hashlib
import hmac
import json
from decimal import Decimal
from typing import Dict, Optional
from django.conf import settings
from .base import PaymentGateway


class PesepayGateway(PaymentGateway):
    """
    Pesepay Payment Gateway Integration
    
    To use this gateway:
    1. Sign up at: https://www.pesepay.com
    2. Get your API Key and Secret
    3. Add to settings:
       PESEPAY_API_KEY = 'your_api_key'
       PESEPAY_SECRET_KEY = 'your_secret_key'
       PESEPAY_API_URL = 'https://api.pesepay.com'  # or sandbox
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.api_key = config.get('api_key') or getattr(settings, 'PESEPAY_API_KEY', '')
        self.secret_key = config.get('secret_key') or getattr(settings, 'PESEPAY_SECRET_KEY', '')
        self.api_url = config.get('api_url') or getattr(settings, 'PESEPAY_API_URL', 'https://api.pesepay.com')
        self.sandbox = config.get('sandbox', False) or getattr(settings, 'PESEPAY_SANDBOX', False)
        
        if self.sandbox:
            self.api_url = 'https://sandbox.pesepay.com'  # Update with actual sandbox URL
    
    def _create_signature(self, data: Dict) -> str:
        """Create signature for Pesepay request"""
        # Sort keys and create signature string
        sorted_keys = sorted(data.keys())
        signature_string = ''.join([f"{key}{data[key]}" for key in sorted_keys])
        signature_string += self.secret_key
        
        return hashlib.sha256(signature_string.encode()).hexdigest()
    
    def initiate_payment(self, amount: Decimal, currency: str, reference: str,
                        customer_phone: str, customer_email: str = '',
                        description: str = '', **kwargs) -> Dict:
        """Initiate Pesepay payment"""
        try:
            phone = self.format_phone_number(customer_phone)
            
            payment_data = {
                'amount': float(amount),
                'currency': currency,
                'reference': reference,
                'customer_phone': phone,
                'customer_email': customer_email,
                'description': description or f'Payment for {reference}',
                'return_url': kwargs.get('return_url', f'{settings.SITE_URL}/payments/return/'),
                'cancel_url': kwargs.get('cancel_url', f'{settings.SITE_URL}/payments/cancel/'),
            }
            
            # Create signature
            signature = self._create_signature(payment_data)
            payment_data['signature'] = signature
            
            # Make API request
            response = requests.post(
                f'{self.api_url}/api/v1/payments',
                json=payment_data,
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                    'Content-Type': 'application/json',
                },
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                return {
                    'success': True,
                    'payment_url': data.get('payment_url', ''),
                    'payment_reference': data.get('payment_reference', reference),
                    'gateway_response': data,
                }
            else:
                error_msg = response.json().get('message', 'Payment initiation failed')
                return {
                    'success': False,
                    'error': error_msg,
                    'gateway_response': response.json() if response.content else {}
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Pesepay payment error: {str(e)}'
            }
    
    def verify_payment(self, payment_reference: str) -> Dict:
        """Verify payment status"""
        try:
            response = requests.get(
                f'{self.api_url}/api/v1/payments/{payment_reference}',
                headers={
                    'Authorization': f'Bearer {self.api_key}',
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'PENDING').upper()
                
                status_map = {
                    'SUCCESS': 'COMPLETED',
                    'COMPLETED': 'COMPLETED',
                    'PENDING': 'PENDING',
                    'FAILED': 'FAILED',
                    'CANCELLED': 'FAILED',
                }
                
                return {
                    'success': True,
                    'status': status_map.get(status, 'PENDING'),
                    'amount': Decimal(str(data.get('amount', 0))),
                    'gateway_response': data,
                }
            else:
                return {
                    'success': False,
                    'error': f'Payment verification failed: {response.status_code}',
                    'status': 'PENDING',
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Pesepay verification error: {str(e)}',
                'status': 'PENDING',
            }
    
    def handle_webhook(self, request_data: Dict) -> Dict:
        """Handle Pesepay webhook callback"""
        try:
            # Verify signature
            received_signature = request_data.pop('signature', '')
            calculated_signature = self._create_signature(request_data)
            
            if received_signature != calculated_signature:
                return {
                    'success': False,
                    'error': 'Signature verification failed'
                }
            
            payment_reference = request_data.get('reference', '')
            status = request_data.get('status', 'PENDING').upper()
            amount = Decimal(str(request_data.get('amount', 0)))
            
            status_map = {
                'SUCCESS': 'COMPLETED',
                'COMPLETED': 'COMPLETED',
                'PENDING': 'PENDING',
                'FAILED': 'FAILED',
            }
            
            return {
                'success': True,
                'payment_reference': payment_reference,
                'status': status_map.get(status, 'PENDING'),
                'amount': amount,
                'gateway_response': request_data,
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Pesepay webhook error: {str(e)}',
            }

