from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.conf import settings
import json
from .models import PaymentMethod, Transaction, Wallet, EscrowTransaction, Subscription, WithdrawalRequest
from .forms import PaymentMethodForm, WithdrawalRequestForm


@login_required
def wallet(request):
    """User wallet view"""
    try:
        wallet = request.user.wallet
    except Wallet.DoesNotExist:
        wallet = Wallet.objects.create(user=request.user)
    
    # Get recent transactions
    recent_transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')[:10]
    
    context = {
        'wallet': wallet,
        'recent_transactions': recent_transactions,
    }
    
    return render(request, 'payments/wallet.html', context)


@login_required
def payment_methods(request):
    """Manage payment methods"""
    payment_methods = PaymentMethod.objects.filter(user=request.user)
    
    if request.method == 'POST':
        form = PaymentMethodForm(request.POST)
        if form.is_valid():
            payment_method = form.save(commit=False)
            payment_method.user = request.user
            payment_method.save()
            messages.success(request, 'Payment method added successfully!')
            return redirect('payments:payment_methods')
    else:
        form = PaymentMethodForm()
    
    context = {
        'payment_methods': payment_methods,
        'form': form,
    }
    
    return render(request, 'payments/payment_methods.html', context)


@login_required
def subscription(request):
    """Subscription page for women"""
    if request.user.user_type != 'F':
        messages.error(request, 'This page is only for female users.')
        return redirect('accounts:profile')
    
    # Check if user already has active subscription
    active_subscription = Subscription.objects.filter(
        user=request.user,
        subscription_type='WOMEN_ACCESS',
        is_active=True,
        end_date__gt=timezone.now()
    ).first()
    
    if active_subscription:
        messages.info(request, 'You already have an active subscription.')
        return redirect('bids:browse_bids')
    
    if request.method == 'POST':
        # Process subscription payment
        amount = settings.MJOLOBID_SETTINGS['WOMEN_SUBSCRIPTION_FEE']
        
        # Create transaction
        transaction = Transaction.objects.create(
            user=request.user,
            transaction_type='SUBSCRIPTION',
            amount=amount,
            description='Women Access Subscription',
            status='PENDING'
        )
        
        # For demo purposes, mark as completed immediately
        transaction.status = 'COMPLETED'
        transaction.processed_at = timezone.now()
        transaction.save()
        
        # Create subscription
        subscription = Subscription.objects.create(
            user=request.user,
            subscription_type='WOMEN_ACCESS',
            amount=amount,
            payment_transaction=transaction
        )
        
        # Update user subscription status
        request.user.subscription_active = True
        request.user.subscription_expires = subscription.end_date
        request.user.save()
        
        messages.success(request, 'Subscription activated successfully!')
        return redirect('bids:browse_bids')
    
    return render(request, 'payments/subscription.html')


@login_required
def premium_upgrade(request):
    """Premium upgrade page"""
    if request.user.is_premium:
        messages.info(request, 'You already have premium access.')
        return redirect('accounts:profile')
    
    if request.method == 'POST':
        # Process premium upgrade payment
        amount = 20.00  # Premium subscription fee
        
        # Create transaction
        transaction = Transaction.objects.create(
            user=request.user,
            transaction_type='PREMIUM_UPGRADE',
            amount=amount,
            description='Premium Upgrade',
            status='PENDING'
        )
        
        # For demo purposes, mark as completed immediately
        transaction.status = 'COMPLETED'
        transaction.processed_at = timezone.now()
        transaction.save()
        
        # Create subscription
        subscription = Subscription.objects.create(
            user=request.user,
            subscription_type='PREMIUM_MEN' if request.user.user_type == 'M' else 'PREMIUM_WOMEN',
            amount=amount,
            payment_transaction=transaction
        )
        
        # Update user premium status
        request.user.is_premium = True
        request.user.premium_expires = subscription.end_date
        request.user.save()
        
        messages.success(request, 'Premium upgrade successful!')
        return redirect('accounts:profile')
    
    return render(request, 'payments/premium_upgrade.html')


@login_required
def withdrawal_request(request):
    """Request withdrawal"""
    try:
        wallet = request.user.wallet
    except Wallet.DoesNotExist:
        wallet = Wallet.objects.create(user=request.user)
    
    if request.method == 'POST':
        form = WithdrawalRequestForm(request.POST)
        if form.is_valid():
            withdrawal_request = form.save(commit=False)
            withdrawal_request.user = request.user
            
            # Check if user has sufficient balance
            if not wallet.can_withdraw(withdrawal_request.amount):
                messages.error(request, 'Insufficient balance or amount below minimum withdrawal.')
                return redirect('payments:withdrawal_request')
            
            # Create transaction
            transaction = Transaction.objects.create(
                user=request.user,
                transaction_type='WITHDRAWAL',
                amount=withdrawal_request.amount,
                description=f'Withdrawal to {withdrawal_request.payment_method.get_payment_type_display()}',
                status='PENDING'
            )
            
            withdrawal_request.transaction = transaction
            withdrawal_request.save()
            
            # Deduct from wallet
            wallet.balance -= withdrawal_request.amount
            wallet.save()
            
            messages.success(request, 'Withdrawal request submitted successfully!')
            return redirect('payments:wallet')
    else:
        form = WithdrawalRequestForm()
        form.fields['payment_method'].queryset = PaymentMethod.objects.filter(user=request.user, is_verified=True)
    
    context = {
        'form': form,
        'wallet': wallet,
    }
    
    return render(request, 'payments/withdrawal_request.html', context)


@login_required
def transaction_history(request):
    """Transaction history"""
    transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    from django.core.paginator import Paginator
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'payments/transaction_history.html', context)


@login_required
@csrf_exempt
def process_payment(request):
    """Process payment via AJAX"""
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            amount = data.get('amount')
            payment_method_id = data.get('payment_method_id')
            description = data.get('description', 'Payment')
            
            if not amount or not payment_method_id:
                return JsonResponse({'status': 'error', 'message': 'Missing required fields'})
            
            # Get payment method
            payment_method = get_object_or_404(PaymentMethod, id=payment_method_id, user=request.user)
            
            # Create transaction
            transaction = Transaction.objects.create(
                user=request.user,
                transaction_type='BID_PAYMENT',
                amount=amount,
                description=description,
                payment_method=payment_method,
                status='PENDING'
            )
            
            # For demo purposes, mark as completed immediately
            transaction.status = 'COMPLETED'
            transaction.processed_at = timezone.now()
            transaction.save()
            
            return JsonResponse({
                'status': 'success',
                'transaction_id': transaction.transaction_id,
                'message': 'Payment processed successfully'
            })
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})
    
    return JsonResponse({'status': 'error', 'message': 'Invalid request method'})


@login_required
def escrow_details(request, bid_id):
    """View escrow details for a bid"""
    from bids.models import Bid
    bid = get_object_or_404(Bid, id=bid_id)
    
    # Check if user is involved in this bid
    if request.user != bid.user and request.user != bid.accepted_by:
        messages.error(request, 'You cannot view escrow details for this bid.')
        return redirect('bids:my_bids')
    
    try:
        escrow = bid.escrow
    except EscrowTransaction.DoesNotExist:
        messages.error(request, 'No escrow found for this bid.')
        return redirect('bids:bid_detail', bid_id=bid_id)
    
    context = {
        'bid': bid,
        'escrow': escrow,
    }
    
    return render(request, 'payments/escrow_details.html', context)
