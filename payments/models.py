from django.db import models
from django.utils import timezone
from accounts.models import User
from bids.models import Bid
from decimal import Decimal


class PaymentMethod(models.Model):
    """User payment methods"""
    
    PAYMENT_TYPE_CHOICES = [
        ('ECOCASH', 'EcoCash'),
        ('ONEMONEY', 'OneMoney'),
        ('INNBUCKS', 'InnBucks'),
        ('BANK_TRANSFER', 'Bank Transfer'),
        ('CARD', 'Credit/Debit Card'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    account_number = models.CharField(max_length=100)  # Phone number, account number, etc.
    account_name = models.CharField(max_length=200)
    is_primary = models.BooleanField(default=False)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['user', 'payment_type', 'account_number']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_payment_type_display()}"


class Transaction(models.Model):
    """Transaction model for all payments"""
    
    TRANSACTION_TYPE_CHOICES = [
        ('BID_PAYMENT', 'Bid Payment'),
        ('SUBSCRIPTION', 'Subscription Fee'),
        ('COMMISSION', 'Platform Commission'),
        ('WITHDRAWAL', 'Withdrawal'),
        ('REFUND', 'Refund'),
        ('REFERRAL_BONUS', 'Referral Bonus'),
        ('PREMIUM_UPGRADE', 'Premium Upgrade'),
    ]
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
        ('REFUNDED', 'Refunded'),
    ]
    
    # Transaction details
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    transaction_id = models.CharField(max_length=100, unique=True)
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='USD')
    
    # Status and processing
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Related objects
    related_bid = models.ForeignKey(Bid, on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    
    # Payment gateway details
    gateway_transaction_id = models.CharField(max_length=200, blank=True)
    gateway_response = models.JSONField(default=dict, blank=True)
    
    # Description and metadata
    description = models.TextField()
    metadata = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    processed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.transaction_id} - {self.user.username} - ${self.amount}"
    
    def save(self, *args, **kwargs):
        if not self.transaction_id:
            import uuid
            self.transaction_id = f"TXN_{uuid.uuid4().hex[:12].upper()}"
        super().save(*args, **kwargs)


class Wallet(models.Model):
    """User wallet for holding funds"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    frozen_balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)  # For escrow
    total_deposited = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    total_withdrawn = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Wallet settings
    is_active = models.BooleanField(default=True)
    auto_withdraw = models.BooleanField(default=False)
    min_withdrawal_amount = models.DecimalField(max_digits=10, decimal_places=2, default=10.00)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s Wallet - ${self.balance}"
    
    @property
    def available_balance(self):
        return self.balance - self.frozen_balance
    
    def can_withdraw(self, amount):
        return self.available_balance >= amount and amount >= self.min_withdrawal_amount


class EscrowTransaction(models.Model):
    """Escrow transactions for bid payments"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('HELD', 'Held'),
        ('RELEASED', 'Released'),
        ('REFUNDED', 'Refunded'),
        ('DISPUTED', 'Disputed'),
    ]
    
    bid = models.OneToOneField(Bid, on_delete=models.CASCADE, related_name='escrow')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    commission_amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    
    # Parties involved
    payer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='escrow_payments')
    payee = models.ForeignKey(User, on_delete=models.CASCADE, related_name='escrow_receipts')
    
    # Transaction references
    payment_transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='escrow_payment')
    release_transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='escrow_release')
    commission_transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True, related_name='escrow_commission')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    held_at = models.DateTimeField(null=True, blank=True)
    released_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Escrow for {self.bid.title} - ${self.amount}"
    
    def hold_funds(self):
        """Hold funds in escrow"""
        if self.status == 'PENDING':
            self.status = 'HELD'
            self.held_at = timezone.now()
            self.save()
            
            # Freeze funds in payer's wallet
            payer_wallet = self.payer.wallet
            payer_wallet.frozen_balance += self.amount
            payer_wallet.save()
    
    def release_funds(self):
        """Release funds from escrow"""
        if self.status == 'HELD':
            self.status = 'RELEASED'
            self.released_at = timezone.now()
            self.save()
            
            # Release funds to payee
            payee_wallet = self.payee.wallet
            payee_wallet.balance += self.amount - self.commission_amount
            payee_wallet.total_deposited += self.amount - self.commission_amount
            payee_wallet.save()
            
            # Unfreeze funds from payer's wallet
            payer_wallet = self.payer.wallet
            payer_wallet.frozen_balance -= self.amount
            payer_wallet.save()
    
    def refund_funds(self):
        """Refund funds to payer"""
        if self.status in ['PENDING', 'HELD']:
            self.status = 'REFUNDED'
            self.save()
            
            # Refund to payer's wallet
            payer_wallet = self.payer.wallet
            payer_wallet.balance += self.amount
            payer_wallet.frozen_balance -= self.amount
            payer_wallet.save()


class Subscription(models.Model):
    """User subscriptions"""
    
    SUBSCRIPTION_TYPE_CHOICES = [
        ('WOMEN_ACCESS', 'Women Access'),
        ('PREMIUM_MEN', 'Premium Men'),
        ('PREMIUM_WOMEN', 'Premium Women'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscriptions')
    subscription_type = models.CharField(max_length=20, choices=SUBSCRIPTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    
    # Subscription period
    start_date = models.DateTimeField(default=timezone.now)
    end_date = models.DateTimeField()
    is_active = models.BooleanField(default=True)
    
    # Payment details
    payment_transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.get_subscription_type_display()}"
    
    @property
    def is_expired(self):
        return timezone.now() > self.end_date
    
    def save(self, *args, **kwargs):
        if not self.end_date:
            if self.subscription_type == 'WOMEN_ACCESS':
                self.end_date = self.start_date + timezone.timedelta(days=30)
            else:
                self.end_date = self.start_date + timezone.timedelta(days=30)
        super().save(*args, **kwargs)


class WithdrawalRequest(models.Model):
    """Withdrawal requests"""
    
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('PROCESSING', 'Processing'),
        ('COMPLETED', 'Completed'),
        ('FAILED', 'Failed'),
        ('CANCELLED', 'Cancelled'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='withdrawal_requests')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.CASCADE)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='PENDING')
    transaction = models.ForeignKey(Transaction, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Processing details
    processed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='processed_withdrawals')
    processed_at = models.DateTimeField(null=True, blank=True)
    notes = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Withdrawal ${self.amount} - {self.user.username}"
