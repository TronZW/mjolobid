from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncDay, TruncWeek
from django.contrib import messages
from accounts.models import User
from bids.models import Bid, EventPromotion
from payments.models import Transaction, Wallet, ManualPayment, Subscription
from datetime import datetime, timedelta
from decimal import Decimal


def is_admin(user):
    """Check if user is admin"""
    return user.is_staff or user.is_superuser


@login_required
@user_passes_test(is_admin)
def dashboard(request):
    """Main admin dashboard"""
    
    # Get current date and time
    now = timezone.now()
    today = now.date()
    week_ago = now - timedelta(days=7)
    month_ago = now - timedelta(days=30)
    
    # User statistics
    total_users = User.objects.count()
    online_users = User.objects.filter(last_seen__gte=now - timedelta(minutes=5)).count()
    daily_logins = User.objects.filter(last_login__date=today).count()
    new_users_today = User.objects.filter(date_joined__date=today).count()
    
    # User breakdown by type
    male_users = User.objects.filter(user_type='M').count()
    female_users = User.objects.filter(user_type='F').count()
    
    # Premium users
    premium_users = User.objects.filter(is_premium=True).count()
    verified_users = User.objects.filter(is_verified=True).count()
    
    # Bid statistics
    total_bids = Bid.objects.count()
    pending_bids = Bid.objects.filter(status='PENDING').count()
    accepted_bids = Bid.objects.filter(status='ACCEPTED').count()
    completed_bids = Bid.objects.filter(status='COMPLETED').count()
    
    # Today's bids
    bids_today = Bid.objects.filter(created_at__date=today).count()
    matched_bids_today = Bid.objects.filter(
        status='ACCEPTED',
        accepted_at__date=today
    ).count()
    
    # Revenue statistics
    weekly_revenue = Transaction.objects.filter(
        transaction_type__in=['COMMISSION', 'SUBSCRIPTION', 'PREMIUM_UPGRADE'],
        status='COMPLETED',
        created_at__gte=week_ago
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    monthly_revenue = Transaction.objects.filter(
        transaction_type__in=['COMMISSION', 'SUBSCRIPTION', 'PREMIUM_UPGRADE'],
        status='COMPLETED',
        created_at__gte=month_ago
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Revenue breakdown
    commission_revenue = Transaction.objects.filter(
        transaction_type='COMMISSION',
        status='COMPLETED',
        created_at__gte=week_ago
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    subscription_revenue = Transaction.objects.filter(
        transaction_type='SUBSCRIPTION',
        status='COMPLETED',
        created_at__gte=week_ago
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    premium_revenue = Transaction.objects.filter(
        transaction_type='PREMIUM_UPGRADE',
        status='COMPLETED',
        created_at__gte=week_ago
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    # Recent activity
    recent_bids = Bid.objects.order_by('-created_at')[:5]
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_transactions = Transaction.objects.filter(
        transaction_type__in=['COMMISSION', 'SUBSCRIPTION', 'PREMIUM_UPGRADE']
    ).order_by('-created_at')[:5]
    
    # Top users
    top_bidders = User.objects.filter(
        user_type='M',
        bids_posted__isnull=False
    ).annotate(
        bid_count=Count('bids_posted')
    ).order_by('-bid_count')[:5]
    
    top_earners = User.objects.filter(
        user_type='F',
        total_earned__gt=0
    ).order_by('-total_earned')[:5]
    
    # Event promotions
    active_promotions = EventPromotion.objects.filter(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now
    ).count()
    
    context = {
        # User metrics
        'total_users': total_users,
        'online_users': online_users,
        'daily_logins': daily_logins,
        'new_users_today': new_users_today,
        'male_users': male_users,
        'female_users': female_users,
        'premium_users': premium_users,
        'verified_users': verified_users,
        
        # Bid metrics
        'total_bids': total_bids,
        'pending_bids': pending_bids,
        'accepted_bids': accepted_bids,
        'completed_bids': completed_bids,
        'bids_today': bids_today,
        'matched_bids_today': matched_bids_today,
        
        # Revenue metrics
        'weekly_revenue': weekly_revenue,
        'monthly_revenue': monthly_revenue,
        'commission_revenue': commission_revenue,
        'subscription_revenue': subscription_revenue,
        'premium_revenue': premium_revenue,
        
        # Recent activity
        'recent_bids': recent_bids,
        'recent_users': recent_users,
        'recent_transactions': recent_transactions,
        
        # Top users
        'top_bidders': top_bidders,
        'top_earners': top_earners,
        
        # Other metrics
        'active_promotions': active_promotions,
    }
    
    return render(request, 'admin_dashboard/dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def users_analytics(request):
    """User analytics page"""
    
    # User growth over time
    user_growth = User.objects.extra(
        select={'day': 'date(date_joined)'}
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    # User type distribution
    user_types = User.objects.values('user_type').annotate(
        count=Count('id')
    )
    
    # Premium vs free users
    premium_distribution = {
        'premium': User.objects.filter(is_premium=True).count(),
        'free': User.objects.filter(is_premium=False).count(),
    }
    
    # Verification status
    verification_status = {
        'verified': User.objects.filter(is_verified=True).count(),
        'unverified': User.objects.filter(is_verified=False).count(),
    }
    
    # Top cities
    top_cities = User.objects.values('city').annotate(
        count=Count('id')
    ).order_by('-count')[:10]
    
    context = {
        'user_growth': user_growth,
        'user_types': user_types,
        'premium_distribution': premium_distribution,
        'verification_status': verification_status,
        'top_cities': top_cities,
    }
    
    return render(request, 'admin_dashboard/users_analytics.html', context)


@login_required
@user_passes_test(is_admin)
def bids_analytics(request):
    """Bid analytics page"""
    
    # Bid status distribution
    bid_status = Bid.objects.values('status').annotate(
        count=Count('id')
    )
    
    # Bids by category
    bids_by_category = Bid.objects.values('event_category__name').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Bid amounts distribution
    bid_amounts = Bid.objects.extra(
        select={
            'amount_range': "CASE WHEN bid_amount < 20 THEN 'Under $20' WHEN bid_amount < 50 THEN '$20-$50' WHEN bid_amount < 100 THEN '$50-$100' ELSE 'Over $100' END"
        }
    ).values('amount_range').annotate(
        count=Count('id')
    )
    
    # Daily bid activity
    daily_bids = Bid.objects.extra(
        select={'day': 'date(created_at)'}
    ).values('day').annotate(
        count=Count('id')
    ).order_by('day')
    
    # Average bid amounts
    avg_bid_amount = Bid.objects.aggregate(
        avg_amount=Sum('bid_amount') / Count('id')
    )['avg_amount'] or 0
    
    context = {
        'bid_status': bid_status,
        'bids_by_category': bids_by_category,
        'bid_amounts': bid_amounts,
        'daily_bids': daily_bids,
        'avg_bid_amount': avg_bid_amount,
    }
    
    return render(request, 'admin_dashboard/bids_analytics.html', context)


@login_required
@user_passes_test(is_admin)
def revenue_analytics(request):
    """Revenue analytics page"""
    
    # Revenue by type
    revenue_by_type = Transaction.objects.filter(
        transaction_type__in=['COMMISSION', 'SUBSCRIPTION', 'PREMIUM_UPGRADE'],
        status='COMPLETED'
    ).values('transaction_type').annotate(
        total=Sum('amount')
    )
    
    # Daily revenue
    daily_revenue = Transaction.objects.filter(
        transaction_type__in=['COMMISSION', 'SUBSCRIPTION', 'PREMIUM_UPGRADE'],
        status='COMPLETED'
    ).extra(
        select={'day': 'date(created_at)'}
    ).values('day').annotate(
        total=Sum('amount')
    ).order_by('day')
    
    # Monthly revenue
    monthly_revenue = Transaction.objects.filter(
        transaction_type__in=['COMMISSION', 'SUBSCRIPTION', 'PREMIUM_UPGRADE'],
        status='COMPLETED'
    ).extra(
        select={'month': 'date_trunc(\'month\', created_at)'}
    ).values('month').annotate(
        total=Sum('amount')
    ).order_by('month')
    
    # Top earning users
    top_earners = User.objects.filter(
        user_type='F',
        total_earned__gt=0
    ).order_by('-total_earned')[:10]
    
    # Top spending users
    top_spenders = User.objects.filter(
        user_type='M',
        total_spent__gt=0
    ).order_by('-total_spent')[:10]
    
    context = {
        'revenue_by_type': revenue_by_type,
        'daily_revenue': daily_revenue,
        'monthly_revenue': monthly_revenue,
        'top_earners': top_earners,
        'top_spenders': top_spenders,
    }
    
    return render(request, 'admin_dashboard/revenue_analytics.html', context)


@login_required
@user_passes_test(is_admin)
def api_metrics(request):
    """API endpoint for real-time metrics"""
    
    now = timezone.now()
    today = now.date()
    
    # Real-time metrics
    online_users = User.objects.filter(last_seen__gte=now - timedelta(minutes=5)).count()
    daily_logins = User.objects.filter(last_login__date=today).count()
    bids_today = Bid.objects.filter(created_at__date=today).count()
    matched_bids_today = Bid.objects.filter(
        status='ACCEPTED',
        accepted_at__date=today
    ).count()
    
    # Weekly revenue
    week_ago = now - timedelta(days=7)
    weekly_revenue = Transaction.objects.filter(
        transaction_type__in=['COMMISSION', 'SUBSCRIPTION', 'PREMIUM_UPGRADE'],
        status='COMPLETED',
        created_at__gte=week_ago
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    return JsonResponse({
        'online_users': online_users,
        'daily_logins': daily_logins,
        'bids_today': bids_today,
        'matched_bids_today': matched_bids_today,
        'weekly_revenue': float(weekly_revenue),
        'timestamp': now.isoformat(),
    })


@login_required
@user_passes_test(is_admin)
def verify_payments(request):
    """Admin view to verify manual payments"""
    status_filter = request.GET.get('status', 'PENDING')
    
    payments = ManualPayment.objects.all()
    
    if status_filter:
        payments = payments.filter(status=status_filter)
    
    payments = payments.order_by('-created_at')
    
    # Get counts for tabs
    pending_count = ManualPayment.objects.filter(status='PENDING').count()
    verified_count = ManualPayment.objects.filter(status='VERIFIED').count()
    rejected_count = ManualPayment.objects.filter(status='REJECTED').count()
    
    context = {
        'payments': payments,
        'status_filter': status_filter,
        'pending_count': pending_count,
        'verified_count': verified_count,
        'rejected_count': rejected_count,
    }
    
    return render(request, 'admin_dashboard/verify_payments.html', context)


@login_required
@user_passes_test(is_admin)
def verify_payment_action(request, payment_id):
    """Handle payment verification action (verify or reject)"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'Invalid request method'})
    
    payment = get_object_or_404(ManualPayment, id=payment_id)
    action = request.POST.get('action')  # 'verify' or 'reject'
    admin_notes = request.POST.get('admin_notes', '')
    
    if action == 'verify':
        # Verify the payment
        payment.status = 'VERIFIED'
        payment.verified_by = request.user
        payment.verified_at = timezone.now()
        if admin_notes:
            payment.admin_notes = admin_notes
        payment.save()
        
        # Update transaction
        if payment.transaction:
            payment.transaction.status = 'COMPLETED'
            payment.transaction.processed_at = timezone.now()
            payment.transaction.save()
        
        # Activate subscription if it's a subscription payment
        if payment.transaction_type == 'SUBSCRIPTION':
            # Check if subscription already exists
            subscription = Subscription.objects.filter(
                user=payment.user,
                payment_transaction=payment.transaction
            ).first()
            
            if not subscription:
                # Create subscription
                subscription = Subscription.objects.create(
                    user=payment.user,
                    subscription_type='WOMEN_ACCESS',
                    amount=payment.amount,
                    payment_transaction=payment.transaction,
                    is_active=True
                )
            else:
                subscription.is_active = True
                subscription.save()
            
            # Update user subscription status
            payment.user.subscription_active = True
            payment.user.subscription_expires = subscription.end_date
            payment.user.save()

            # --- Affiliate referral bonus logic ---
            # If this is a female user who was referred by someone, and this is
            # a qualifying subscription ($3 Women Access), award a $0.30 bonus.
            try:
                referred_user = payment.user
                referrer = referred_user.referred_by
                amount = Decimal(str(payment.amount or 0))

                if (
                    referrer
                    and referred_user.user_type == 'F'
                    and amount >= Decimal('3.00')
                ):
                    # Avoid double-paying for the same referred user
                    already_paid = Transaction.objects.filter(
                        user=referrer,
                        transaction_type='REFERRAL_BONUS',
                        metadata__referred_user_id=referred_user.id,
                    ).exists()

                    if not already_paid:
                        bonus_amount = Decimal('0.30')
                        bonus_txn = Transaction.objects.create(
                            user=referrer,
                            transaction_type='REFERRAL_BONUS',
                            amount=bonus_amount,
                            description=f'Referral bonus for {referred_user.username} subscription',
                            status='COMPLETED',
                            metadata={
                                'referred_user_id': referred_user.id,
                                'referred_username': referred_user.username,
                                'subscription_transaction_id': payment.transaction.id if payment.transaction else None,
                            },
                        )

                        # Update referrer stats
                        referrer.referral_earnings += bonus_amount
                        referrer.total_referrals += 1
                        referrer.save(update_fields=['referral_earnings', 'total_referrals'])

                        # Notify referrer
                        try:
                            from notifications.utils import send_notification

                            send_notification(
                                user=referrer,
                                title='Referral Bonus Earned!',
                                message=f'You earned ${bonus_amount} because {referred_user.username} subscribed for Women Access.',
                                notification_type='REFERRAL_BONUS',
                                related_object_type='transaction',
                                related_object_id=bonus_txn.id,
                            )
                        except Exception:
                            # Do not break payment flow if notification fails
                            pass
            except Exception:
                # Do not break payment flow for any affiliate errors
                pass
        
        # Send in-app notification to user
        try:
            from notifications.utils import send_notification
            send_notification(
                user=payment.user,
                title='Payment Verified - Subscription Activated!',
                message=f'Your payment of ${payment.amount} has been verified. Your subscription is now active and you can accept bids!',
                notification_type='PAYMENT_RECEIVED',
                related_object_type='transaction',
                related_object_id=payment.transaction.id if payment.transaction else None
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Failed to send notification: {str(e)}')
        
        # Send success email to user
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            
            send_mail(
                subject='Payment Verified - Subscription Activated!',
                message=f'''
Hello {payment.user.username},

Great news! Your payment of ${payment.amount} has been verified and your subscription is now active.

Transaction Details:
- Amount: ${payment.amount}
- EcoCash Reference: {payment.ecocash_reference}
- Verified At: {payment.verified_at.strftime("%Y-%m-%d %H:%M")}

You can now accept bids on MjoloBid!

Thank you for subscribing.
MjoloBid Team
                ''',
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@mjolobid.com'),
                recipient_list=[payment.user.email],
                fail_silently=True,
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Failed to send verification success email: {str(e)}')
        
        messages.success(request, f'Payment verified successfully! Subscription activated for {payment.user.username}.')
        
    elif action == 'reject':
        # Reject the payment
        payment.status = 'REJECTED'
        payment.verified_by = request.user
        payment.verified_at = timezone.now()
        payment.admin_notes = admin_notes or 'Payment verification failed'
        payment.save()
        
        # Send in-app notification to user
        try:
            from notifications.utils import send_notification
            send_notification(
                user=payment.user,
                title='Payment Verification Failed',
                message=f'Your payment verification was unsuccessful. Reason: {payment.admin_notes or "Please check your EcoCash reference and try again."}',
                notification_type='PAYMENT_SENT',
                related_object_type='transaction',
                related_object_id=payment.transaction.id if payment.transaction else None
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Failed to send notification: {str(e)}')
        
        # Send rejection email to user
        try:
            from django.core.mail import send_mail
            from django.conf import settings
            
            send_mail(
                subject='Payment Verification Failed',
                message=f'''
Hello {payment.user.username},

Unfortunately, your payment verification could not be completed.

Transaction Details:
- Amount: ${payment.amount}
- EcoCash Reference: {payment.ecocash_reference}

Reason: {payment.admin_notes or 'Payment verification failed. Please check your EcoCash reference number and try again.'}

If you believe this is an error, please contact support with your EcoCash reference number.

MjoloBid Team
                ''',
                from_email=getattr(settings, 'DEFAULT_FROM_EMAIL', 'noreply@mjolobid.com'),
                recipient_list=[payment.user.email],
                fail_silently=True,
            )
        except Exception as e:
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f'Failed to send rejection email: {str(e)}')
        
        messages.warning(request, f'Payment rejected for {payment.user.username}.')
    else:
        return JsonResponse({'success': False, 'error': 'Invalid action'})
    
    return redirect('admin_dashboard:verify_payments')
