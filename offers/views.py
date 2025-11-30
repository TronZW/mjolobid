from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q, Max
from django.core.paginator import Paginator
from django.conf import settings
from django.db import close_old_connections
from threading import Thread
from .models import Offer, OfferBid, OfferView
from .forms import OfferForm, OfferBidForm
from accounts.models import User, UserGallery
from bids.models import EventCategory
from notifications.utils import send_notification


def _send_new_offer_notifications_async(offer_id, creator_id):
    """
    Background task to send 'new offer' notifications to all active male users.
    Runs in a separate thread so the HTTP request can return quickly.
    """
    # Ensure this thread has a clean DB connection
    close_old_connections()

    try:
        offer = Offer.objects.get(id=offer_id)
        creator = User.objects.get(id=creator_id)
    except (Offer.DoesNotExist, User.DoesNotExist):
        return

    # Get all active male users with valid email
    male_users = User.objects.filter(
        user_type='M',
        is_active=True,
        email__isnull=False
    ).exclude(email='')

    for male_user in male_users.iterator():
        try:
            send_notification(
                user=male_user,
                title='New Offer Available!',
                message=f'{creator.username} created a new offer: {offer.title} - Starting at ${offer.minimum_bid}',
                notification_type='OFFER_BID',
                related_object_type='offer',
                related_object_id=offer.id
            )
        except Exception as e:
            # Log and continue; one failure shouldn't stop others
            print(f"Error sending new offer notification to {male_user.username}: {e}")


@login_required
def create_offer(request):
    """Girls create offers"""
    if request.user.user_type != 'F':
        messages.error(request, 'Only female users can create offers.')
        return redirect('offers:browse_offers')
    
    if request.method == 'POST':
        form = OfferForm(request.POST)
        if form.is_valid():
            offer = form.save(commit=False)
            offer.user = request.user
            
            # Handle event category
            event_category_choice = form.cleaned_data.get('event_category')
            custom_category = form.cleaned_data.get('custom_category')
            
            if event_category_choice and event_category_choice != '':
                if event_category_choice == 'other' and custom_category:
                    category, created = EventCategory.objects.get_or_create(
                        name=custom_category,
                        defaults={
                            'icon': '✨',
                            'description': f'Custom category: {custom_category}',
                            'is_active': True
                        }
                    )
                    offer.event_category = category
                else:
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
                        offer.event_category = category
            
            offer.save()
            
            # Fire-and-forget: send notifications in a background thread
            try:
                Thread(
                    target=_send_new_offer_notifications_async,
                    args=(offer.id, request.user.id),
                    daemon=True
                ).start()
            except Exception as e:
                print(f"Error starting async new offer notifications: {e}")
            
            messages.success(request, 'Offer created successfully!')
            return redirect('offers:my_offers')
    else:
        form = OfferForm()
    
    context = {
        'form': form,
    }
    return render(request, 'offers/create_offer.html', context)


@login_required
def browse_offers(request):
    """Men browse available offers"""
    if request.user.user_type != 'M':
        messages.error(request, 'Only male users can browse offers.')
        return redirect('offers:my_offers')
    
    # Get filter parameters
    raw_category = request.GET.get('category')
    min_amount = request.GET.get('min_amount')
    max_amount = request.GET.get('max_amount')
    raw_location = request.GET.get('location')
    sort_by = request.GET.get('sort_by', 'created_at')
    
    # Normalize filters
    def _normalize(value: str):
        if not value:
            return None
        v = value.strip()
        if v.lower() in ('none', 'all', 'any'):
            return None
        return v
    
    category = _normalize(raw_category)
    location = _normalize(raw_location)
    
    # Base queryset - only show offers from female users
    offers = Offer.objects.filter(
        status='PENDING',
        user__user_type='F',
        user__is_active=True
    ).exclude(user=request.user)
    
    # Filter by expiration
    now = timezone.now()
    offers = offers.filter(
        Q(expires_at__isnull=True) | Q(expires_at__gt=now)
    )
    
    # Apply filters
    if category:
        offers = offers.filter(event_category__name=category)
    
    if min_amount:
        try:
            min_amount_float = float(min_amount)
            offers = offers.filter(minimum_bid__gte=min_amount_float)
        except ValueError:
            pass
    
    if max_amount:
        try:
            max_amount_float = float(max_amount)
            offers = offers.filter(minimum_bid__lte=max_amount_float)
        except ValueError:
            pass
    
    if location:
        offers = offers.filter(event_location__icontains=location)
    
    # Apply sorting
    if sort_by == 'amount':
        offers = offers.order_by('-minimum_bid')
    elif sort_by == 'date':
        offers = offers.order_by('event_date', 'available_date')
    else:
        offers = offers.order_by('-created_at')
    
    # Calculate distances if user has location
    if request.user.latitude and request.user.longitude:
        for offer in offers:
            offer.distance = offer.distance_from_user(
                request.user.latitude,
                request.user.longitude
            )
    
    # Pagination
    paginator = Paginator(offers, 12)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get categories for filter
    categories = EventCategory.objects.filter(is_active=True)
    
    context = {
        'page_obj': page_obj,
        'categories': categories,
        'current_filters': {
            'category': category or '',
            'min_amount': min_amount or '',
            'max_amount': max_amount or '',
            'location': location or '',
            'sort_by': sort_by or 'created_at',
        }
    }
    
    return render(request, 'offers/browse_offers.html', context)


@login_required
def offer_detail(request, offer_id):
    """View offer details"""
    offer = get_object_or_404(Offer, id=offer_id)
    
    # Calculate distance
    if request.user.latitude and request.user.longitude:
        offer.distance = offer.distance_from_user(
            request.user.latitude,
            request.user.longitude
        )
    
    # Get offer creator's profile and gallery
    offer_creator = offer.user
    gallery_images = UserGallery.objects.filter(user=offer_creator).order_by('-is_primary', '-uploaded_at')[:6]
    
    # Track view if user is male and not the offer owner
    if request.user.user_type == 'M' and request.user != offer.user:
        OfferView.objects.get_or_create(offer=offer, viewer=request.user)
    
    # Get existing bid if user already bid
    existing_bid = None
    if request.user.user_type == 'M' and request.user != offer.user:
        try:
            existing_bid = OfferBid.objects.get(offer=offer, bidder=request.user)
        except OfferBid.DoesNotExist:
            pass
    
    # Get all bids (only show to offer creator)
    all_bids = None
    if request.user == offer.user:
        all_bids = OfferBid.objects.filter(offer=offer).select_related('bidder').order_by('-bid_amount', '-created_at')
    
    context = {
        'offer': offer,
        'offer_creator': offer_creator,
        'gallery_images': gallery_images,
        'existing_bid': existing_bid,
        'all_bids': all_bids,
        'can_bid': (
            request.user.user_type == 'M' and
            offer.status == 'PENDING' and
            request.user != offer.user and
            not existing_bid
        ),
        'can_message': (
            offer.status == 'ACCEPTED' and (
                request.user == offer.user or 
                request.user == offer.accepted_by
            )
        ),
    }
    
    return render(request, 'offers/offer_detail.html', context)


@login_required
def place_bid_on_offer(request, offer_id):
    """Men place bids on offers"""
    if request.user.user_type != 'M':
        messages.error(request, 'Only male users can place bids on offers.')
        return redirect('offers:browse_offers')
    
    offer = get_object_or_404(Offer, id=offer_id)
    
    if offer.status != 'PENDING':
        messages.error(request, 'This offer is no longer available.')
        return redirect('offers:browse_offers')
    
    if offer.user == request.user:
        messages.error(request, 'You cannot bid on your own offer.')
        return redirect('offers:offer_detail', offer_id=offer_id)
    
    # Check if user already bid
    existing_bid = OfferBid.objects.filter(offer=offer, bidder=request.user).first()
    if existing_bid:
        messages.info(request, 'You have already placed a bid on this offer.')
        return redirect('offers:offer_detail', offer_id=offer_id)
    
    if request.method == 'POST':
        form = OfferBidForm(request.POST, offer=offer)
        if form.is_valid():
            bid = form.save(commit=False)
            bid.offer = offer
            bid.bidder = request.user
            bid.save()
            
            # Send notification to offer creator
            from notifications.utils import send_notification
            send_notification(
                user=offer.user,
                title='New Bid on Your Offer!',
                message=f'{request.user.username} has placed a ${bid.bid_amount} bid on your offer: {offer.title}',
                notification_type='OFFER_BID',
                related_object_type='offer',
                related_object_id=offer.id
            )
            
            messages.success(request, f'Your bid of ${bid.bid_amount} has been placed successfully!')
            return redirect('offers:offer_detail', offer_id=offer_id)
    else:
        form = OfferBidForm(offer=offer)
    
    # Get offer creator's profile and gallery for preview
    offer_creator = offer.user
    gallery_images = UserGallery.objects.filter(user=offer_creator).order_by('-is_primary', '-uploaded_at')[:6]
    
    context = {
        'form': form,
        'offer': offer,
        'offer_creator': offer_creator,
        'gallery_images': gallery_images,
    }
    
    return render(request, 'offers/place_bid.html', context)


@login_required
def my_offers(request):
    """View user's created offers (for girls)"""
    if request.user.user_type != 'F':
        messages.error(request, 'Only female users can create offers.')
        return redirect('offers:browse_offers')
    
    offers = Offer.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(offers, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'offers/my_offers.html', context)


@login_required
def view_offer_bids(request, offer_id):
    """Girl views all bids on her offer"""
    offer = get_object_or_404(Offer, id=offer_id)
    
    if offer.user != request.user:
        messages.error(request, 'You can only view bids on your own offers.')
        return redirect('offers:my_offers')
    
    bids = OfferBid.objects.filter(offer=offer).select_related('bidder').order_by('-bid_amount', '-created_at')
    
    context = {
        'offer': offer,
        'bids': bids,
    }
    
    return render(request, 'offers/view_offer_bids.html', context)


@login_required
def choose_bid(request, offer_id, bid_id):
    """Girl chooses a bid (accepts an offer bid)"""
    offer = get_object_or_404(Offer, id=offer_id)
    
    if offer.user != request.user:
        messages.error(request, 'You can only choose bids on your own offers.')
        return redirect('offers:my_offers')
    
    if offer.status != 'PENDING':
        messages.error(request, 'This offer is no longer available for selection.')
        return redirect('offers:my_offers')
    
    bid = get_object_or_404(OfferBid, id=bid_id, offer=offer, status='PENDING')
    
    if request.method == 'POST':
        # Mark selected bid as SELECTED
        bid.status = 'SELECTED'
        bid.save()
        
        # Mark all other bids as REJECTED
        OfferBid.objects.filter(
            offer=offer,
            status='PENDING'
        ).exclude(id=bid_id).update(status='REJECTED')
        
        # Update offer status to ACCEPTED
        offer.status = 'ACCEPTED'
        offer.accepted_by = bid.bidder
        offer.accepted_at = timezone.now()
        offer.save()
        
        # Send notifications
        from notifications.utils import send_notification
        
        # Notify selected bidder
        send_notification(
            user=bid.bidder,
            title='Your Bid Was Selected!',
            message=f'Congratulations! {request.user.username} has selected your bid for their offer: {offer.title}',
            notification_type='OFFER_ACCEPTED',
            related_object_type='offer',
            related_object_id=offer.id
        )
        
        # Notify rejected bidders
        rejected_bids = OfferBid.objects.filter(offer=offer, status='REJECTED')
        for rejected_bid in rejected_bids:
            send_notification(
                user=rejected_bid.bidder,
                title='Bid Selection Update',
                message=f'Sorry, {request.user.username} has selected someone else for their offer: {offer.title}',
                notification_type='BID_CANCELLED',
                related_object_type='offer',
                related_object_id=offer.id
            )
        
        messages.success(request, f'You have selected {bid.bidder.username}\'s bid!')
        return redirect('offers:my_offers')
    
    # Get bidder's profile and gallery for preview
    bidder = bid.bidder
    gallery_images = UserGallery.objects.filter(user=bidder).order_by('-is_primary', '-uploaded_at')[:6]
    
    context = {
        'offer': offer,
        'bid': bid,
        'bidder': bidder,
        'gallery_images': gallery_images,
    }
    
    return render(request, 'offers/choose_bid.html', context)


@login_required
def my_offer_bids(request):
    """View bids user placed on offers (for men)"""
    if request.user.user_type != 'M':
        messages.error(request, 'Only male users can place bids on offers.')
        return redirect('offers:my_offers')
    
    bids = OfferBid.objects.filter(bidder=request.user).select_related('offer', 'offer__user').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(bids, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
    }
    
    return render(request, 'offers/my_offer_bids.html', context)


@login_required
def edit_offer(request, offer_id):
    """Edit an existing offer"""
    if request.user.user_type != 'F':
        messages.error(request, 'Only female users can edit offers.')
        return redirect('offers:browse_offers')
    
    offer = get_object_or_404(Offer, id=offer_id, user=request.user)
    
    if offer.status != 'PENDING':
        messages.error(request, 'You can only edit pending offers.')
        return redirect('offers:my_offers')
    
    if request.method == 'POST':
        form = OfferForm(request.POST, instance=offer)
        if form.is_valid():
            offer = form.save(commit=False)
            
            # Handle event category
            event_category_choice = form.cleaned_data.get('event_category')
            custom_category = form.cleaned_data.get('custom_category')
            
            if event_category_choice and event_category_choice != '':
                if event_category_choice == 'other' and custom_category:
                    category, created = EventCategory.objects.get_or_create(
                        name=custom_category,
                        defaults={
                            'icon': '✨',
                            'description': f'Custom category: {custom_category}',
                            'is_active': True
                        }
                    )
                    offer.event_category = category
                else:
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
                        offer.event_category = category
            else:
                offer.event_category = None
            
            offer.save()
            messages.success(request, 'Offer updated successfully!')
            return redirect('offers:my_offers')
    else:
        form = OfferForm(instance=offer)
    
    context = {
        'form': form,
        'offer': offer,
    }
    
    return render(request, 'offers/edit_offer.html', context)


@login_required
def delete_offer(request, offer_id):
    """Delete an offer"""
    offer = get_object_or_404(Offer, id=offer_id, user=request.user)
    
    if offer.status != 'PENDING':
        messages.error(request, 'You can only delete pending offers.')
        return redirect('offers:my_offers')
    
    if request.method == 'POST':
        # Notify all bidders
        from notifications.utils import send_notification
        bids = OfferBid.objects.filter(offer=offer)
        for bid in bids:
            send_notification(
                user=bid.bidder,
                title='Offer Cancelled',
                message=f'{request.user.username} has cancelled their offer: {offer.title}',
                notification_type='BID_CANCELLED',
                related_object_type='offer',
                related_object_id=offer.id
            )
        
        offer.delete()
        messages.success(request, 'Offer deleted successfully!')
        return redirect('offers:my_offers')
    
    context = {
        'offer': offer,
    }
    
    return render(request, 'offers/delete_offer.html', context)
