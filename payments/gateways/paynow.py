"""
Paynow Payment Gateway Integration
Paynow is a popular payment aggregator in Zimbabwe supporting:
- EcoCash
- OneMoney
- TeleCash
- ZimSwitch
- VISA/MasterCard
- PayPal
"""
import requests
import hashlib
from decimal import Decimal
from typing import Dict, Optional
from django.conf import settings
from .base import PaymentGateway


class PaynowGateway(PaymentGateway):
    """
    Paynow Payment Gateway Integration
    
    To use this gateway:
    1. Sign up at: https://www.paynow.co.zw
    2. Get your Integration ID and Integration Key
    3. Add to settings:
       PAYNOW_INTEGRATION_ID = 'your_integration_id'
       PAYNOW_INTEGRATION_KEY = 'your_integration_key'
       PAYNOW_API_URL = 'https://www.paynow.co.zw/Interface/API'  # or sandbox
    """
    
    def __init__(self, config: Optional[Dict] = None):
        super().__init__(config)
        self.integration_id = config.get('integration_id') or getattr(settings, 'PAYNOW_INTEGRATION_ID', '')
        self.integration_key = config.get('integration_key') or getattr(settings, 'PAYNOW_INTEGRATION_KEY', '')
        self.api_url = config.get('api_url') or getattr(settings, 'PAYNOW_API_URL', 'https://www.paynow.co.zw/Interface/API')
        self.sandbox = config.get('sandbox', False) or getattr(settings, 'PAYNOW_SANDBOX', False)
        
        if self.sandbox:
            self.api_url = 'https://sandbox.paynow.co.zw/Interface/API'  # Update with actual sandbox URL
    
    def _create_hash(self, values: Dict) -> str:
        """Create hash for Paynow request"""
        hash_string = ''
        for key in sorted(values.keys()):
            if key != 'hash':
                hash_string += str(values[key])
        hash_string += self.integration_key
        return hashlib.sha512(hash_string.encode()).hexdigest().upper()
    
    def initiate_payment(self, amount: Decimal, currency: str, reference: str,
                        customer_phone: str, customer_email: str = '',
                        description: str = '', **kwargs) -> Dict:
        """Initiate Paynow payment"""
        try:
            phone = self.format_phone_number(customer_phone)
            
            # Prepare payment data
            payment_data = {
                'resulturl': kwargs.get('return_url', f'{settings.SITE_URL}/payments/return/'),
                'returnurl': kwargs.get('return_url', f'{settings.SITE_URL}/payments/return/'),
                'reference': reference,
                'amount': str(amount),
                'id': self.integration_id,
                'additionalinfo': description or f'Payment for {reference}',
                'authemail': customer_email or '',
                'status': 'Message',
            }
            
            # Create hash
            payment_data['hash'] = self._create_hash(payment_data)
            
            # Make API request
            response = requests.post(
                f'{self.api_url}/InitiateTransaction',
                data=payment_data,
                timeout=30
            )
            
            if response.status_code == 200:
                # Parse response (Paynow returns key=value format)
                response_data = {}
                for line in response.text.split('&'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        response_data[key] = value
                
                if response_data.get('status') == 'Ok':
                    # Verify hash
                    response_hash = response_data.pop('hash', '')
                    calculated_hash = self._create_hash(response_data)
                    
                    if response_hash == calculated_hash:
                        return {
                            'success': True,
                            'payment_url': response_data.get('browserurl', ''),
                            'payment_reference': response_data.get('pollurl', '').split('/')[-1] if response_data.get('pollurl') else reference,
                            'gateway_response': response_data,
                        }
                    else:
                        return {
                            'success': False,
                            'error': 'Hash verification failed'
                        }
                else:
                    return {
                        'success': False,
                        'error': response_data.get('error', 'Payment initiation failed'),
                        'gateway_response': response_data,
                    }
            else:
                return {
                    'success': False,
                    'error': f'HTTP {response.status_code}: Payment initiation failed'
                }
                
        except Exception as e:
            return {
                'success': False,
                'error': f'Paynow payment error: {str(e)}'
            }
    
    def verify_payment(self, payment_reference: str) -> Dict:
        """Verify payment status via Paynow poll URL"""
        try:
            poll_url = f'{self.api_url}/GetTransactionStatus/{payment_reference}'
            
            response = requests.get(poll_url, timeout=30)
            
            if response.status_code == 200:
                # Parse response
                response_data = {}
                for line in response.text.split('&'):
                    if '=' in line:
                        key, value = line.split('=', 1)
                        response_data[key] = value
                
                status = response_data.get('status', 'Unknown').upper()
                status_map = {
                    'PAID': 'COMPLETED',
                    'CANCELLED': 'FAILED',
                    'CREATED': 'PENDING',
                }
                
                return {
                    'success': True,
                    'status': status_map.get(status, 'PENDING'),
                    'amount': Decimal(str(response_data.get('amount', 0))),
                    'gateway_response': response_data,
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
                'error': f'Paynow verification error: {str(e)}',
                'status': 'PENDING',
            }
    
    def handle_webhook(self, request_data: Dict) -> Dict:
        """Handle Paynow webhook callback"""
        try:
            # Verify hash
            received_hash = request_data.pop('hash', '')
            calculated_hash = self._create_hash(request_data)
            
            if received_hash != calculated_hash:
                return {
                    'success': False,
                    'error': 'Hash verification failed'
                }
            
            payment_reference = request_data.get('reference', '')
            status = request_data.get('status', 'PENDING').upper()
            amount = Decimal(str(request_data.get('amount', 0)))
            
            status_map = {
                'PAID': 'COMPLETED',
                'CANCELLED': 'FAILED',
                'CREATED': 'PENDING',
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
                'error': f'Paynow webhook error: {str(e)}',
            }

