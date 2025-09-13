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
]
