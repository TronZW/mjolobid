from django.shortcuts import render
from django.contrib.auth.decorators import login_required, user_passes_test
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Count, Sum, Q
from django.db.models.functions import TruncDay, TruncWeek
from accounts.models import User
from bids.models import Bid, EventPromotion
from payments.models import Transaction, Wallet
from datetime import datetime, timedelta


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
