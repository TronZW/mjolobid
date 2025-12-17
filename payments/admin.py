from django.contrib import admin
from .models import PaymentMethod, Transaction, Wallet, EscrowTransaction, Subscription, WithdrawalRequest, ManualPayment


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    list_display = ('user', 'payment_type', 'account_number', 'is_primary', 'is_verified', 'created_at')
    list_filter = ('payment_type', 'is_primary', 'is_verified', 'created_at')
    search_fields = ('user__username', 'account_number', 'account_name')
    raw_id_fields = ('user',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ('transaction_id', 'user', 'transaction_type', 'amount', 'status', 'created_at')
    list_filter = ('transaction_type', 'status', 'created_at')
    search_fields = ('transaction_id', 'user__username', 'description')
    raw_id_fields = ('user', 'payment_method', 'related_bid')
    readonly_fields = ('transaction_id', 'created_at', 'updated_at')


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    list_display = ('user', 'balance', 'frozen_balance', 'available_balance', 'is_active')
    list_filter = ('is_active', 'auto_withdraw')
    search_fields = ('user__username',)
    raw_id_fields = ('user',)
    readonly_fields = ('available_balance',)


@admin.register(EscrowTransaction)
class EscrowTransactionAdmin(admin.ModelAdmin):
    list_display = ('bid', 'amount', 'status', 'payer', 'payee', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('bid__title', 'payer__username', 'payee__username')
    raw_id_fields = ('bid', 'payer', 'payee', 'payment_transaction', 'release_transaction', 'commission_transaction')


@admin.register(Subscription)
class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('user', 'subscription_type', 'amount', 'start_date', 'end_date', 'is_active')
    list_filter = ('subscription_type', 'is_active', 'created_at')
    search_fields = ('user__username',)
    raw_id_fields = ('user', 'payment_transaction')


@admin.register(WithdrawalRequest)
class WithdrawalRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'payment_method', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('user__username',)
    raw_id_fields = ('user', 'payment_method', 'transaction', 'processed_by')


@admin.register(ManualPayment)
class ManualPaymentAdmin(admin.ModelAdmin):
    list_display = ('user', 'amount', 'transaction_type', 'ecocash_reference', 'sender_name', 'status', 'created_at', 'verified_by')
    list_filter = ('status', 'transaction_type', 'created_at')
    search_fields = ('user__username', 'ecocash_reference', 'sender_name', 'sender_phone')
    raw_id_fields = ('user', 'transaction', 'verified_by')
    readonly_fields = ('created_at', 'updated_at')
    fieldsets = (
        ('Payment Information', {
            'fields': ('user', 'transaction', 'transaction_type', 'amount', 'status')
        }),
        ('Payment Proof', {
            'fields': ('sender_name', 'ecocash_reference', 'sender_phone')
        }),
        ('Verification', {
            'fields': ('verified_by', 'verified_at', 'admin_notes')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at')
        }),
    )
