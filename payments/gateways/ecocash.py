"""
EcoCash Payment Gateway Integration
EcoCash is Zimbabwe's most popular mobile money service
"""
import requests
import hashlib
import hmac
import json
from decimal import Decimal
from typing import Dict, Optional
from django.conf import settings
from .base import PaymentGateway


class EcoCashGateway(PaymentGateway):
    """
    EcoCash API Integration
    
    To use this gateway:
    1. Register as EcoCash merchant at: https://www.ecocash.co.zw/merchants
    2. Get your API credentials (Client ID and Secret)
    3. Add to settings:
       ECOCASH_CLIENT_ID = 'your_client_id'
       ECOCASH_CLIENT_SECRET = 'your_client_secret'
       ECOCASH_MERCHANT_ID = 'your_merchant_id'
       ECOCASH_API_URL = 'https://api.ecocash.co.zw'  # or sandbox URL
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.client_id = config.get('client_id') or getattr(settings, 'ECOCASH_CLIENT_ID', '')
        self.client_secret = config.get('client_secret') or getattr(settings, 'ECOCASH_CLIENT_SECRET', '')
        self.merchant_id = config.get('merchant_id') or getattr(settings, 'ECOCASH_MERCHANT_ID', '')
        self.api_url = config.get('api_url') or getattr(settings, 'ECOCASH_API_URL', 'https://api.ecocash.co.zw')
        self.sandbox = config.get('sandbox', False) or getattr(settings, 'ECOCASH_SANDBOX', False)
        
        if self.sandbox:
            self.api_url = 'https://sandbox.ecocash.co.zw'  # Update with actual sandbox URL
    
    def _get_access_token(self) -> Optional[str]:
        """Get OAuth access token from EcoCash API"""
        try:
            response = requests.post(
                f'{self.api_url}/oauth/token',
                data={
                    'grant_type': 'client_credentials',
                    'client_id': self.client_id,
                    'client_secret': self.client_secret,
                },
                headers={'Content-Type': 'application/x-www-form-urlencoded'},
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get('access_token')
            else:
                print(f"EcoCash token error: {response.status_code} - {response.text}")
                return None
        except Exception as e:
            print(f"EcoCash token exception: {str(e)}")
            return None
    
    def initiate_payment(self, amount: Decimal, currency: str, reference: str,
                        customer_phone: str, customer_email: str = '',
                        description: str = '', **kwargs) -> Dict:
        """
        Initiate EcoCash payment
        
        EcoCash uses USSD push - user receives prompt on their phone
        """
        try:
            # Format phone number
            phone = self.format_phone_number(customer_phone)
            
            # Get access token
            access_token = self._get_access_token()
            if not access_token:
                return {
                    'success': False,
                    'error': 'Failed to authenticate with EcoCash API'
                }
            
            # Prepare payment request
            payment_data = {
                'merchant_id': self.merchant_id,
                'amount': str(amount),
                'currency': currency,
                'reference': reference,
                'customer_phone': phone,
                'description': description or f'Payment for {reference}',
                'callback_url': kwargs.get('callback_url', f'{settings.SITE_URL}/payments/webhook/ecocash/'),
            }
            
            # Make API request
            response = requests.post(
                f'{self.api_url}/api/v1/payments',
                json=payment_data,
                headers={
                    'Authorization': f'Bearer {access_token}',
                    'Content-Type': 'application/json',
                },
                timeout=30
            )
            
            if response.status_code in [200, 201]:
                data = response.json()
                return {
                    'success': True,
                    'payment_reference': data.get('payment_reference', reference),
                    'gateway_response': data,
                    'message': 'Payment request sent. Please check your phone and approve the EcoCash prompt.',
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
                'error': f'EcoCash payment error: {str(e)}'
            }
    
    def verify_payment(self, payment_reference: str) -> Dict:
        """Verify payment status"""
        try:
            access_token = self._get_access_token()
            if not access_token:
                return {
                    'success': False,
                    'error': 'Failed to authenticate with EcoCash API'
                }
            
            response = requests.get(
                f'{self.api_url}/api/v1/payments/{payment_reference}',
                headers={
                    'Authorization': f'Bearer {access_token}',
                },
                timeout=30
            )
            
            if response.status_code == 200:
                data = response.json()
                status = data.get('status', 'PENDING').upper()
                
                # Map EcoCash status to our status
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
                'error': f'EcoCash verification error: {str(e)}',
                'status': 'PENDING',
            }
    
    def handle_webhook(self, request_data: Dict) -> Dict:
        """Handle EcoCash webhook callback"""
        try:
            # Verify webhook signature (if provided by EcoCash)
            # This is a placeholder - implement actual signature verification
            payment_reference = request_data.get('payment_reference') or request_data.get('reference')
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
                'error': f'EcoCash webhook error: {str(e)}',
            }
    
    def get_supported_currencies(self) -> list:
        return ['USD', 'ZWL']
    
    def get_minimum_amount(self) -> Decimal:
        return Decimal('1.00')

