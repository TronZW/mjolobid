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
from .models import Bid, EventCategory, BidMessage, BidReview, EventPromotion, BidView, BidImage
from .forms import BidForm, BidReviewForm, EventPromotionForm
from accounts.models import User


@login_required
def browse_bids(request):
    """Browse available bids for women"""
    # Prevent admin users from accessing browse bids
    if request.user.is_staff or request.user.is_superuser:
        messages.error(request, 'Admin users cannot browse bids.')
        return redirect('/dashboard/')
    
    # Subscription gate disabled for browsing (can be re-enabled via settings flag)
    if (
        request.user.user_type == 'F'
        and not request.user.subscription_active
        and getattr(settings, 'REQUIRE_SUBSCRIPTION_FOR_BROWSING', False)
    ):
        return redirect('payments:subscription')
    
    # Get filter parameters
    raw_category = request.GET.get('category')
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')
    raw_location = request.GET.get('location')
    sort_by = request.GET.get('sort_by', 'created_at')

    # Normalize filters (ignore placeholders like 'None', 'All', 'Any')
    def _normalize(value: str):
        if not value:
            return None
        v = value.strip()
        if v.lower() in ('none', 'all', 'any'):
            return None
        return v

    category = _normalize(raw_category)
    location = _normalize(raw_location)
    
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

    # Fallback: if filters resulted in no bids, show latest pending bids
    if not bids.exists():
        bids = Bid.objects.filter(status='PENDING').exclude(user=request.user).order_by('-created_at')[:12]
    
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
            'category': category or '',
            'min_amount': min_amount or '',
            'max_amount': max_amount or '',
            'location': location or '',
            'sort_by': sort_by or 'created_at',
        }
    }
    
    return render(request, 'bids/browse_bids.html', context)


@login_required
def bid_detail(request, bid_id):
    """View bid details"""
    bid = get_object_or_404(Bid, id=bid_id)
    
    # Subscription gate disabled for viewing details (toggle via settings flag)
    if (
        request.user.user_type == 'F'
        and not request.user.subscription_active
        and getattr(settings, 'REQUIRE_SUBSCRIPTION_FOR_BROWSING', False)
    ):
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
    
    # Track view if user is female and not the bid owner
    # Also notify the bid owner when someone views their bid
    if request.user.user_type == 'F' and request.user != bid.user:
        bid_view, created = BidView.objects.get_or_create(bid=bid, viewer=request.user)
        if created:
            # Only notify on first view per user/bid
            try:
                from notifications.utils import send_notification
                send_notification(
                    user=bid.user,
                    title='Your bid was viewed',
                    message=f'{request.user.username} viewed your bid: {bid.title}',
                    notification_type='OFFER_BID',
                    related_object_type='bid',
                    related_object_id=bid.id
                )
            except ImportError:
                pass
    
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
def upcoming_events(request):
    """List upcoming events from admins/organizers (not bids)."""
    now = timezone.now()
    events = EventPromotion.objects.filter(
        is_active=True,
        start_date__lte=now,
        end_date__gte=now,
        event_date__gte=now,
    ).order_by('-priority', 'event_date')

    context = {
        'events': events,
    }
    return render(request, 'bids/upcoming_events.html', context)


@login_required
def add_event(request):
    """Add a new event promotion (admin only)"""
    if not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Only administrators can add events.')
        return redirect('bids:upcoming_events')
    
    if request.method == 'POST':
        form = EventPromotionForm(request.POST, request.FILES)
        if form.is_valid():
            event = form.save()
            messages.success(request, f'Event "{event.title}" has been added successfully!')
            return redirect('bids:upcoming_events')
    else:
        form = EventPromotionForm()
    
    context = {
        'form': form,
    }
    return render(request, 'bids/add_event.html', context)


@login_required
def post_bid_for_event(request, event_id):
    """Create a bid based on an admin event (male users only)"""
    if request.user.user_type != 'M' or request.user.is_staff or request.user.is_superuser:
        messages.error(request, 'Only male users can create bids for events.')
        return redirect('bids:upcoming_events')
    
    event = get_object_or_404(EventPromotion, id=event_id, is_active=True)
    
    if request.method == 'POST':
        form = BidForm(request.POST, request.FILES)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.user = request.user
            bid.event_location = event.location
            bid.event_address = event.location  # Use location as address for now
            
            # Handle event category
            event_category_choice = form.cleaned_data.get('event_category')
            custom_category = form.cleaned_data.get('custom_category')
            
            if event_category_choice == 'other' and custom_category:
                # Create or get custom category
                category, created = EventCategory.objects.get_or_create(
                    name=custom_category,
                    defaults={
                        'icon': '✨',
                        'description': f'Custom category: {custom_category}',
                        'is_active': True
                    }
                )
                bid.event_category = category
            else:
                # Map choice to category name and get/create category
                category_mapping = {
                    'club_night': 'Club Night',
                    'concert': 'Concert',
                    'restaurant': 'Restaurant',
                    'movie': 'Movie',
                    'sports_event': 'Sports Event',
                    'beach_day': 'Beach Day',
                    'shopping': 'Shopping',
                    'art_exhibition': 'Art Exhibition',
                    'hiking': 'Hiking',
                }
                
                if event_category_choice in category_mapping:
                    category_name = category_mapping[event_category_choice]
                    category, created = EventCategory.objects.get_or_create(
                        name=category_name,
                        defaults={
                            'icon': '🎉',
                            'description': f'{category_name} events',
                            'is_active': True
                        }
                    )
                    bid.event_category = category
            
            bid.save()
            messages.success(request, f'Bid for "{event.title}" has been created successfully!')
            return redirect('bids:my_bids')
    else:
        # Pre-fill form with event data
        initial_data = {
            'title': f'Bid for {event.title}',
            'description': f'I would like to attend {event.title} on {event.event_date.strftime("%B %d, %Y")} at {event.location}.',
            'event_date': event.event_date,
            'event_location': event.location,
            'event_address': event.location,
        }
        form = BidForm(initial=initial_data)
    
    context = {
        'form': form,
        'event': event,
    }
    return render(request, 'bids/post_bid_for_event.html', context)


@login_required
def accept_bid(request, bid_id):
    """Accept a bid - now allows multiple acceptances"""
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
    
    # Check if user already accepted this bid
    from bids.models import BidAcceptance
    existing_acceptance = BidAcceptance.objects.filter(bid=bid, accepted_by=request.user).first()
    
    if existing_acceptance:
        if existing_acceptance.status == 'PENDING':
            messages.info(request, 'You have already accepted this bid!')
        elif existing_acceptance.status == 'WITHDRAWN':
            # Allow re-accepting if previously withdrawn
            existing_acceptance.status = 'PENDING'
            existing_acceptance.accepted_at = timezone.now()
            existing_acceptance.save()
            messages.success(request, f'You have re-accepted the bid for {bid.title}!')
        else:
            messages.info(request, 'You have already accepted this bid!')
        return redirect('bids:browse_bids')
    
    # Create new acceptance
    acceptance = BidAcceptance.objects.create(
        bid=bid,
        accepted_by=request.user,
        status='PENDING'
    )
    
    # Send notification (with email) to bid poster
    try:
        from notifications.utils import send_notification
        send_notification(
            user=bid.user,
            title='New Bid Acceptance!',
            message=f'{request.user.username} has accepted your bid for {bid.title}. You can now choose from your acceptances.',
            notification_type='BID_ACCEPTED',
            related_object_type='bid',
            related_object_id=bid.id
        )
    except ImportError:
        pass
    
    messages.success(request, f'You have accepted the bid for {bid.title}! The bid poster will be notified and can choose from all acceptances.')
    return redirect('bids:my_accepted_bids')


@login_required
def choose_acceptance(request, bid_id):
    """Male user chooses from multiple acceptances"""
    if request.user.user_type != 'M':
        messages.error(request, 'Only male users can choose acceptances.')
        return redirect('bids:browse_bids')
    
    bid = get_object_or_404(Bid, id=bid_id)
    
    if bid.user != request.user:
        messages.error(request, 'You can only choose acceptances for your own bids.')
        return redirect('bids:my_bids')
    
    if bid.status != 'PENDING':
        messages.error(request, 'This bid is no longer available for selection.')
        return redirect('bids:my_bids')
    
    # Get all pending acceptances for this bid
    from bids.models import BidAcceptance
    acceptances = BidAcceptance.objects.filter(bid=bid, status='PENDING').select_related('accepted_by')
    
    if not acceptances.exists():
        messages.error(request, 'No pending acceptances found for this bid.')
        return redirect('bids:my_bids')
    
    if request.method == 'POST':
        acceptance_id = request.POST.get('acceptance_id')
        if not acceptance_id:
            messages.error(request, 'Please select an acceptance.')
            return redirect('bids:choose_acceptance', bid_id=bid_id)
        
        try:
            selected_acceptance = BidAcceptance.objects.get(
                id=acceptance_id, 
                bid=bid, 
                status='PENDING'
            )
        except BidAcceptance.DoesNotExist:
            messages.error(request, 'Invalid acceptance selected.')
            return redirect('bids:choose_acceptance', bid_id=bid_id)
        
        # Mark selected acceptance as SELECTED
        selected_acceptance.status = 'SELECTED'
        selected_acceptance.save()
        
        # Mark all other acceptances as REJECTED
        BidAcceptance.objects.filter(
            bid=bid, 
            status='PENDING'
        ).exclude(id=acceptance_id).update(status='REJECTED')
        
        # Update bid status to ACCEPTED and set accepted_by
        bid.status = 'ACCEPTED'
        bid.accepted_by = selected_acceptance.accepted_by
        bid.accepted_at = timezone.now()
        bid.save()
        
        # Send notifications (with email) to selected and rejected users
        try:
            from notifications.utils import send_notification
            
            # Notify selected girl
            send_notification(
                user=selected_acceptance.accepted_by,
                title='You Were Selected!',
                message=f'Congratulations! {request.user.username} has selected you for their bid: {bid.title}',
                notification_type='BID_ACCEPTED',
                related_object_type='bid',
                related_object_id=bid.id
            )
            
            # Notify rejected girls
            rejected_acceptances = BidAcceptance.objects.filter(bid=bid, status='REJECTED')
            for rejection in rejected_acceptances:
                send_notification(
                    user=rejection.accepted_by,
                    title='Bid Selection Update',
                    message=f'Sorry, {request.user.username} has selected someone else for their bid: {bid.title}',
                    notification_type='BID_CANCELLED',
                    related_object_type='bid',
                    related_object_id=bid.id
                )
        except ImportError:
            pass
        
        messages.success(request, f'You have selected {selected_acceptance.accepted_by.username} for your bid!')
        return redirect('bids:my_bids')
    
    context = {
        'bid': bid,
        'acceptances': acceptances,
    }
    return render(request, 'bids/choose_acceptance.html', context)


@login_required
def male_homepage(request):
    """Male homepage showing women who viewed/accepted their offers"""
    if request.user.user_type != 'M':
        messages.error(request, 'Only male users can access this page.')
        return redirect('bids:browse_bids')
    
    # Get women who have viewed the user's bids
    viewed_women = User.objects.filter(
        user_type='F',
        bid_views__bid__user=request.user
    ).distinct().select_related('profile')
    
    # Get women who have accepted the user's bids (using new BidAcceptance model)
    from bids.models import BidAcceptance
    pending_acceptances = BidAcceptance.objects.filter(
        bid__user=request.user,
        status='PENDING'
    ).select_related('accepted_by', 'bid').order_by('-accepted_at')
    
    # Get women who have accepted the user's bids (old system for completed bids)
    accepted_women = User.objects.filter(
        user_type='F',
        bids_accepted__user=request.user
    ).distinct().select_related('profile')
    
    accepted_bids = Bid.objects.filter(
        user=request.user,
        status='ACCEPTED'
    ).select_related('accepted_by').order_by('-accepted_at')

    # Get recent bids for context
    recent_bids = Bid.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # Get bids with pending acceptances
    bids_with_pending = Bid.objects.filter(
        user=request.user,
        acceptances__status='PENDING'
    ).distinct().order_by('-created_at')
    
    context = {
        'viewed_women': viewed_women,
        'accepted_women': accepted_women,
        'accepted_bids': accepted_bids,
        'recent_bids': recent_bids,
        'pending_acceptances': pending_acceptances,
        'bids_with_pending': bids_with_pending,
    }
    
    return render(request, 'bids/male_homepage.html', context)


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
            
            # Handle event category
            event_category_choice = form.cleaned_data.get('event_category')
            custom_category = form.cleaned_data.get('custom_category')
            
            if event_category_choice == 'other' and custom_category:
                # Create or get custom category
                category, created = EventCategory.objects.get_or_create(
                    name=custom_category,
                    defaults={
                        'icon': '✨',
                        'description': f'Custom category: {custom_category}',
                        'is_active': True
                    }
                )
                bid.event_category = category
            else:
                # Map choice to category name and get/create category
                category_mapping = {
                    'club_night': 'Club Night',
                    'concert': 'Concert',
                    'restaurant': 'Restaurant',
                    'movie': 'Movie',
                    'sports_event': 'Sports Event',
                    'beach_day': 'Beach Day',
                    'shopping': 'Shopping',
                    'art_exhibition': 'Art Exhibition',
                    'hiking': 'Hiking',
                }
                
                if event_category_choice in category_mapping:
                    category_name = category_mapping[event_category_choice]
                    category, created = EventCategory.objects.get_or_create(
                        name=category_name,
                        defaults={
                            'icon': '🎉',
                            'description': f'{category_name} events',
                            'is_active': True
                        }
                    )
                    bid.event_category = category
            
            bid.save()
            
            # Handle images
            images = request.FILES.getlist('images')
            for i, image in enumerate(images):
                BidImage.objects.create(
                    bid=bid,
                    image=image,
                    is_primary=(i == 0)
                )
            
            # Send email notification to all female users about new bid
            try:
                from notifications.utils import send_notification
                from accounts.models import User
                
                # Get all active female users
                female_users = User.objects.filter(
                    user_type='F',
                    is_active=True,
                    email__isnull=False
                ).exclude(email='')
                
                # Send notification to each female user
                for female_user in female_users:
                    send_notification(
                        user=female_user,
                        title='New Bid Available!',
                        message=f'{request.user.username} posted a new bid: {bid.title} - ${bid.bid_amount}',
                        notification_type='OFFER_BID',
                        related_object_type='bid',
                        related_object_id=bid.id
                    )
            except Exception as e:
                print(f"Error sending new bid notifications: {str(e)}")
            
            messages.success(request, 'Bid posted successfully!')
            return redirect('bids:my_bids')
    else:
        form = BidForm()
    
    context = {
        'form': form,
    }
    
    return render(request, 'bids/post_bid.html', context)


@login_required
def edit_bid(request, bid_id):
    """Edit an existing bid (owner only)"""
    if request.user.user_type != 'M':
        messages.error(request, 'Only male users can edit bids.')
        return redirect('bids:browse_bids')

    bid = get_object_or_404(Bid, id=bid_id, user=request.user)

    if request.method == 'POST':
        form = BidForm(request.POST, request.FILES, instance=bid)
        if form.is_valid():
            bid = form.save(commit=False)
            
            # Handle event category
            event_category_choice = form.cleaned_data.get('event_category')
            custom_category = form.cleaned_data.get('custom_category')
            
            if event_category_choice == 'other' and custom_category:
                # Create or get custom category
                category, created = EventCategory.objects.get_or_create(
                    name=custom_category,
                    defaults={
                        'icon': '✨',
                        'description': f'Custom category: {custom_category}',
                        'is_active': True
                    }
                )
                bid.event_category = category
            else:
                # Map choice to category name and get/create category
                category_mapping = {
                    'club_night': 'Club Night',
                    'concert': 'Concert',
                    'restaurant': 'Restaurant',
                    'movie': 'Movie',
                    'sports_event': 'Sports Event',
                    'beach_day': 'Beach Day',
                    'shopping': 'Shopping',
                    'art_exhibition': 'Art Exhibition',
                    'hiking': 'Hiking',
                }
                
                if event_category_choice in category_mapping:
                    category_name = category_mapping[event_category_choice]
                    category, created = EventCategory.objects.get_or_create(
                        name=category_name,
                        defaults={
                            'icon': '🎉',
                            'description': f'{category_name} events',
                            'is_active': True
                        }
                    )
                    bid.event_category = category
            
            bid.save()

            # Optionally handle new images appended to existing ones
            images = request.FILES.getlist('images')
            for image in images:
                BidImage.objects.create(bid=bid, image=image)

            messages.success(request, 'Bid updated successfully!')
            return redirect('bids:my_bids')
    else:
        form = BidForm(instance=bid)

    context = {
        'form': form,
        'bid': bid,
    }

    return render(request, 'bids/edit_bid.html', context)


@login_required
def my_accepted_bids(request):
    """View user's accepted bids"""
    if request.user.user_type == 'M':
        bids = Bid.objects.filter(user=request.user, status='ACCEPTED')
        pending_acceptances = None
    else:
        bids = Bid.objects.filter(accepted_by=request.user, status='ACCEPTED')
        # Also include bids the user has accepted that are awaiting poster selection
        from bids.models import BidAcceptance
        pending_acceptances = (
            BidAcceptance.objects
            .filter(accepted_by=request.user, status='PENDING')
            .select_related('bid', 'bid__user', 'bid__event_category')
            .order_by('-accepted_at')
        )
    
    context = {
        'bids': bids,
        'pending_acceptances': pending_acceptances,
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
