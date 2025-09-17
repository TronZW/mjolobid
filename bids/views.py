from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, F
from django.core.paginator import Paginator
from django.conf import settings
import json
from .models import Bid, EventCategory, BidMessage, BidReview, EventPromotion
from .forms import BidForm, BidReviewForm


@login_required
def browse_bids(request):
    """Browse available bids for women"""
    # Check if user has active subscription
    if request.user.user_type == 'F' and not request.user.subscription_active:
        return redirect('payments:subscription')
    
    # Get filter parameters
    category = request.GET.get('category')
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')
    location = request.GET.get('location')
    sort_by = request.GET.get('sort_by', 'created_at')
    
    # Base queryset
    bids = Bid.objects.filter(
        status='PENDING',
        event_date__gt=timezone.now(),
        expires_at__gt=timezone.now()
    ).exclude(user=request.user)
    
    # Apply filters
    if category:
        bids = bids.filter(event_category__name=category)
    
    if min_amount:
        try:
            min_amount_float = float(min_amount)
            bids = bids.filter(bid_amount__gte=min_amount_float)
        except ValueError:
            pass  # Invalid min_amount value, ignore filter
    
    if max_amount:
        try:
            max_amount_float = float(max_amount)
            bids = bids.filter(bid_amount__lte=max_amount_float)
        except ValueError:
            pass  # Invalid max_amount value, ignore filter
    
    if location:
        bids = bids.filter(event_location__icontains=location)
    
    # Apply sorting
    if sort_by == 'amount':
        bids = bids.order_by('-bid_amount')
    elif sort_by == 'date':
        bids = bids.order_by('event_date')
    else:
        bids = bids.order_by('-created_at')
    
    # Calculate distances if user has location
    if request.user.latitude and request.user.longitude:
        for bid in bids:
            bid.distance = bid.distance_from_user(
                request.user.latitude, 
                request.user.longitude
            )
    
    # Pagination
    paginator = Paginator(bids, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for filter
    categories = EventCategory.objects.filter(is_active=True)
    
    # Get live promotions
    promotions = EventPromotion.objects.filter(
        is_active=True,
        start_date__lte=timezone.now(),
        end_date__gte=timezone.now()
    ).order_by('-priority')[:5]
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'promotions': promotions,
        'current_filters': {
            'category': category,
            'min_amount': min_amount,
            'max_amount': max_amount,
            'location': location,
            'sort_by': sort_by,
        }
    }
    
    return render(request, 'bids/browse_bids.html', context)


@login_required
def bid_detail(request, bid_id):
    """View bid details"""
    bid = get_object_or_404(Bid, id=bid_id)
    
    # Check if user can view this bid
    if request.user.user_type == 'F' and not request.user.subscription_active:
        return redirect('payments:subscription')
    
    # Calculate distance
    if request.user.latitude and request.user.longitude:
        bid.distance = bid.distance_from_user(
            request.user.latitude, 
            request.user.longitude
        )
    
    # Get messages if user is involved
    messages_list = []
    if request.user == bid.user or request.user == bid.accepted_by:
        messages_list = BidMessage.objects.filter(bid=bid).order_by('created_at')
    
    # Get reviews
    reviews = BidReview.objects.filter(bid=bid).order_by('-created_at')
    
    context = {
        'bid': bid,
        'messages': messages_list,
        'reviews': reviews,
        'can_accept': (
            request.user.user_type == 'F' and 
            bid.status == 'PENDING' and 
            request.user != bid.user
        ),
        'can_message': (
            request.user == bid.user or 
            request.user == bid.accepted_by
        ),
    }
    
    return render(request, 'bids/bid_detail.html', context)


@login_required
def accept_bid(request, bid_id):
    """Accept a bid"""
    if request.user.user_type != 'F':
        messages.error(request, 'Only female users can accept bids.')
        return redirect('bids:browse_bids')
    
    bid = get_object_or_404(Bid, id=bid_id)
    
    if bid.status != 'PENDING':
        messages.error(request, 'This bid is no longer available.')
        return redirect('bids:browse_bids')
    
    if bid.user == request.user:
        messages.error(request, 'You cannot accept your own bid.')
        return redirect('bids:browse_bids')
    
    # Accept the bid
    bid.status = 'ACCEPTED'
    bid.accepted_by = request.user
    bid.accepted_at = timezone.now()
    bid.save()
    
    # Send notification
    from notifications.models import Notification
    Notification.objects.create(
        user=bid.user,
        title='Bid Accepted!',
        message=f'{request.user.username} has accepted your bid for {bid.title}',
        notification_type='BID_ACCEPTED',
        related_object_id=bid.id
    )
    
    messages.success(request, f'You have accepted the bid for {bid.title}!')
    return redirect('bids:my_accepted_bids')


@login_required
def my_bids(request):
    """View user's posted bids"""
    if request.user.user_type != 'M':
        messages.error(request, 'Only male users can post bids.')
        return redirect('bids:browse_bids')
    
    bids = Bid.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(bids, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'bids/my_bids.html', context)


@login_required
def post_bid(request):
    """Post a new bid"""
    if request.user.user_type != 'M':
        messages.error(request, 'Only male users can post bids.')
        return redirect('bids:browse_bids')
    
    if request.method == 'POST':
        form = BidForm(request.POST, request.FILES)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.user = request.user
            bid.save()
            
            # Handle images
            images = request.FILES.getlist('images')
            for i, image in enumerate(images):
                BidImage.objects.create(
                    bid=bid,
                    image=image,
                    is_primary=(i == 0)
                )
            
            messages.success(request, 'Bid posted successfully!')
            return redirect('bids:my_bids')
    else:
        form = BidForm()
    
    categories = EventCategory.objects.filter(is_active=True)
    
    context = {
        'form': form,
        'categories': categories,
    }
    
    return render(request, 'bids/post_bid.html', context)


@login_required
def my_accepted_bids(request):
    """View user's accepted bids"""
    if request.user.user_type == 'M':
        bids = Bid.objects.filter(user=request.user, status='ACCEPTED')
    else:
        bids = Bid.objects.filter(accepted_by=request.user, status='ACCEPTED')
    
    context = {
        'bids': bids,
    }
    
    return render(request, 'bids/my_accepted_bids.html', context)


@login_required
def complete_bid(request, bid_id):
    """Mark bid as completed"""
    bid = get_object_or_404(Bid, id=bid_id)
    
    if request.user != bid.user and request.user != bid.accepted_by:
        messages.error(request, 'You cannot complete this bid.')
        return redirect('bids:bid_detail', bid_id=bid_id)
    
    if bid.status != 'ACCEPTED':
        messages.error(request, 'This bid is not accepted yet.')
        return redirect('bids:bid_detail', bid_id=bid_id)
    
    bid.status = 'COMPLETED'
    bid.save()
    
    # Process payment
    from payments.models import Transaction
    Transaction.objects.create(
        user=bid.accepted_by,
        amount=bid.bid_amount - bid.commission_amount,
        transaction_type='BID_PAYMENT',
        status='COMPLETED',
        description=f'Payment for bid: {bid.title}',
        related_bid=bid
    )
    
    # Update user earnings
    bid.accepted_by.total_earned += bid.bid_amount - bid.commission_amount
    bid.accepted_by.save()
    
    messages.success(request, 'Bid marked as completed!')
    return redirect('bids:bid_detail', bid_id=bid_id)


@login_required
def review_bid(request, bid_id):
    """Review a completed bid"""
    bid = get_object_or_404(Bid, id=bid_id)
    
    if request.user != bid.user and request.user != bid.accepted_by:
        messages.error(request, 'You cannot review this bid.')
        return redirect('bids:bid_detail', bid_id=bid_id)
    
    if bid.status != 'COMPLETED':
        messages.error(request, 'This bid is not completed yet.')
        return redirect('bids:bid_detail', bid_id=bid_id)
    
    # Check if user already reviewed
    reviewed_user = bid.accepted_by if request.user == bid.user else bid.user
    if BidReview.objects.filter(bid=bid, reviewer=request.user).exists():
        messages.error(request, 'You have already reviewed this bid.')
        return redirect('bids:bid_detail', bid_id=bid_id)
    
    if request.method == 'POST':
        form = BidReviewForm(request.POST)
        if form.is_valid():
            review = form.save(commit=False)
            review.bid = bid
            review.reviewer = request.user
            review.reviewed_user = reviewed_user
            review.save()
            
            messages.success(request, 'Review submitted!')
            return redirect('bids:bid_detail', bid_id=bid_id)
    else:
        form = BidReviewForm()
    
    context = {
        'form': form,
        'bid': bid,
        'reviewed_user': reviewed_user,
    }
    
    return render(request, 'bids/review_bid.html', context)


@login_required
@csrf_exempt
def boost_bid(request, bid_id):
    """Boost a bid (premium feature)"""
    bid = get_object_or_404(Bid, id=bid_id)
    
    if request.user != bid.user:
        messages.error(request, 'You can only boost your own bids.')
        return redirect('bids:my_bids')
    
    if not request.user.is_premium:
        messages.error(request, 'Premium subscription required to boost bids.')
        return redirect('accounts:premium_upgrade')
    
    # Boost the bid
    bid.is_boosted = True
    bid.boost_expires = timezone.now() + timezone.timedelta(hours=24)
    bid.save()
    
    messages.success(request, 'Bid boosted successfully!')
    return redirect('bids:my_bids')
