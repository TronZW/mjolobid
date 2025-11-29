"""
Payment service for handling payments through various gateways
"""
from decimal import Decimal
from typing import Dict, Optional
from django.conf import settings
from django.utils import timezone
from .models import Transaction
from .gateways import EcoCashGateway, PaynowGateway, PesepayGateway


class PaymentService:
    """Service for processing payments through various gateways"""
    
    GATEWAY_MAP = {
        'ECOCASH': EcoCashGateway,
        'PAYNOW': PaynowGateway,
        'PESEPAY': PesepayGateway,
    }
    
    @classmethod
    def get_gateway(cls, gateway_name: str):
        """Get payment gateway instance"""
        gateway_class = cls.GATEWAY_MAP.get(gateway_name.upper())
        if not gateway_class:
            raise ValueError(f"Unsupported payment gateway: {gateway_name}")
        return gateway_class()
    
    @classmethod
    def initiate_payment(cls, transaction: Transaction, gateway_name: str = 'ECOCASH',
                        customer_phone: str = '', customer_email: str = '') -> Dict:
        """
        Initiate payment for a transaction
        
        Args:
            transaction: Transaction object
            gateway_name: Payment gateway to use ('ECOCASH', 'PAYNOW', 'PESEPAY')
            customer_phone: Customer phone number
            customer_email: Customer email (optional)
        
        Returns:
            Dict with payment initiation result
        """
        try:
            gateway = cls.get_gateway(gateway_name)
            
            # Get customer info from user
            user = transaction.user
            phone = customer_phone or user.phone_number
            email = customer_email or user.email
            
            # Initiate payment
            result = gateway.initiate_payment(
                amount=transaction.amount,
                currency=transaction.currency,
                reference=transaction.transaction_id,
                customer_phone=phone,
                customer_email=email,
                description=transaction.description,
                callback_url=f'{settings.SITE_URL}/payments/webhook/{gateway_name.lower()}/',
                return_url=f'{settings.SITE_URL}/payments/return/?txn={transaction.transaction_id}',
            )
            
            if result.get('success'):
                # Update transaction with gateway info
                transaction.gateway_transaction_id = result.get('payment_reference', transaction.transaction_id)
                transaction.gateway_response = result.get('gateway_response', {})
                transaction.status = 'PROCESSING'
                transaction.save()
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Payment initiation failed: {str(e)}'
            }
    
    @classmethod
    def verify_payment(cls, transaction: Transaction, gateway_name: str = 'ECOCASH') -> Dict:
        """Verify payment status"""
        try:
            gateway = cls.get_gateway(gateway_name)
            
            payment_reference = transaction.gateway_transaction_id or transaction.transaction_id
            result = gateway.verify_payment(payment_reference)
            
            if result.get('success'):
                status = result.get('status')
                
                # Update transaction status
                if status == 'COMPLETED' and transaction.status != 'COMPLETED':
                    transaction.status = 'COMPLETED'
                    transaction.processed_at = timezone.now()
                    transaction.save()
                elif status == 'FAILED' and transaction.status != 'FAILED':
                    transaction.status = 'FAILED'
                    transaction.save()
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Payment verification failed: {str(e)}'
            }
    
    @classmethod
    def handle_webhook(cls, gateway_name: str, request_data: Dict) -> Dict:
        """Handle webhook from payment gateway"""
        try:
            gateway = cls.get_gateway(gateway_name)
            result = gateway.handle_webhook(request_data)
            
            if result.get('success'):
                # Find transaction by reference
                payment_reference = result.get('payment_reference')
                try:
                    transaction = Transaction.objects.get(
                        gateway_transaction_id=payment_reference
                    )
                    
                    # Update transaction
                    status = result.get('status')
                    if status == 'COMPLETED':
                        transaction.status = 'COMPLETED'
                        transaction.processed_at = timezone.now()
                    elif status == 'FAILED':
                        transaction.status = 'FAILED'
                    
                    transaction.gateway_response = result.get('gateway_response', {})
                    transaction.save()
                    
                    # Trigger subscription activation if needed
                    if transaction.transaction_type == 'SUBSCRIPTION':
                        from .models import Subscription
                        from django.utils import timezone
                        from datetime import timedelta
                        
                        subscription = Subscription.objects.filter(
                            payment_transaction=transaction
                        ).first()
                        
                        if subscription and status == 'COMPLETED':
                            subscription.is_active = True
                            subscription.save()
                            
                            # Update user subscription status
                            user = transaction.user
                            user.subscription_active = True
                            user.subscription_expires = subscription.end_date
                            user.save()
                    
                    result['transaction'] = transaction
                    
                except Transaction.DoesNotExist:
                    result['error'] = f'Transaction not found: {payment_reference}'
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': f'Webhook handling failed: {str(e)}'
            }

