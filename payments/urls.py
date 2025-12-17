from django.urls import path
from . import views

app_name = 'payments'

urlpatterns = [
    path('wallet/', views.wallet, name='wallet'),
    path('payment-methods/', views.payment_methods, name='payment_methods'),
    path('subscription/', views.subscription, name='subscription'),
    path('premium-upgrade/', views.premium_upgrade, name='premium_upgrade'),
    path('withdrawal-request/', views.withdrawal_request, name='withdrawal_request'),
    path('transaction-history/', views.transaction_history, name='transaction_history'),
    path('process-payment/', views.process_payment, name='process_payment'),
    path('escrow/<int:bid_id>/', views.escrow_details, name='escrow_details'),
    # Payment gateway webhooks
    path('webhook/ecocash/', views.ecocash_webhook, name='ecocash_webhook'),
    path('webhook/paynow/', views.paynow_webhook, name='paynow_webhook'),
    path('webhook/pesepay/', views.pesepay_webhook, name='pesepay_webhook'),
    # Payment return/cancel URLs
    path('return/', views.payment_return, name='payment_return'),
    path('cancel/', views.payment_cancel, name='payment_cancel'),
    # Manual payment verification
    path('submit-proof/', views.submit_payment_proof, name='submit_payment_proof'),
]
