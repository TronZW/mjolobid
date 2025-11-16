from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse, HttpResponseForbidden
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, Prefetch, Count
from django.core.paginator import Paginator
import json

from django.contrib.auth import get_user_model

from .models import Conversation, Message, MessageAttachment, TypingIndicator
from .forms import MessageForm
from bids.models import Bid, BidAcceptance

User = get_user_model()

# Import Offer model if available
try:
    from offers.models import Offer, OfferBid
except ImportError:
    Offer = None
    OfferBid = None


@login_required
def conversation_list(request):
    """List all conversations for the current user - only 1-on-1 conversations"""
    # Get all conversations where user is a participant
    all_conversations = Conversation.objects.filter(
        participants=request.user,
        is_active=True
    ).select_related('bid', 'bid__user', 'bid__accepted_by', 'offer', 'offer__user', 'offer__accepted_by').prefetch_related(
        'messages__sender', 'participants'
    ).order_by('-updated_at')
    
    # Filter to ensure exactly 2 participants and user is one of them
    conversations = []
    for conversation in all_conversations:
        participants = list(conversation.participants.all())
        # Show conversations with exactly 2 participants where user is one of them
        # OR conversations with messages (in case participant count is off)
        if len(participants) == 2 and request.user in participants:
            conversations.append(conversation)
        elif conversation.messages.exists() and request.user in participants:
            # If conversation has messages but wrong participant count, still show it
            # But ensure it only has 2 participants
            if len(participants) <= 2:
                conversations.append(conversation)
    
    # Add unread counts and latest messages
    for conversation in conversations:
        conversation.unread_count = conversation.get_unread_count(request.user)
        conversation.other_participant = conversation.get_other_participant(request.user)
        # Get the latest message manually to avoid slicing issues
        latest_messages = conversation.messages.select_related('sender').order_by('-created_at')
        conversation.latest_message = latest_messages.first() if latest_messages.exists() else None
    
    context = {
        'conversations': conversations,
    }
    return render(request, 'messaging/conversation_list.html', context)


@login_required
def conversation_detail(request, conversation_id):
    """View individual conversation"""
    conversation = get_object_or_404(
        Conversation.objects.select_related('bid', 'bid__user', 'bid__accepted_by', 'offer', 'offer__user', 'offer__accepted_by'),
        id=conversation_id,
        participants=request.user,
        is_active=True
    )
    
    # Mark all messages as read
    conversation.messages.exclude(
        sender=request.user
    ).filter(
        is_read=False
    ).update(is_read=True, read_at=timezone.now())
    
    # Get messages with pagination
    messages = conversation.messages.select_related('sender').order_by('created_at')
    paginator = Paginator(messages, 50)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get other participant
    other_participant = conversation.get_other_participant(request.user)
    
    context = {
        'conversation': conversation,
        'other_participant': other_participant,
        'messages': page_obj,
        'form': MessageForm(),
    }
    return render(request, 'messaging/conversation_detail.html', context)


@login_required
def start_conversation(request, bid_id):
    """Start a new conversation for a bid - creates a 1-on-1 conversation between two users"""
    bid = get_object_or_404(Bid, id=bid_id)

    # Determine which users are allowed to join a conversation for this bid
    acceptance_user_ids = set(
        BidAcceptance.objects.filter(bid=bid).values_list('accepted_by_id', flat=True)
    )
    acceptance_user_ids.discard(None)

    allowed_user_ids = {bid.user_id}
    if bid.accepted_by_id:
        allowed_user_ids.add(bid.accepted_by_id)
    allowed_user_ids.update(acceptance_user_ids)

    if request.user.id not in allowed_user_ids:
        return HttpResponseForbidden('You cannot start a conversation for this bid')

    # Determine the other participant
    participant_id = request.GET.get('user')
    other_participant = None
    
    if participant_id:
        try:
            participant_id = int(participant_id)
        except (TypeError, ValueError):
            participant_id = None

        if participant_id and participant_id in allowed_user_ids and participant_id != request.user.id:
            other_participant = get_object_or_404(User, id=participant_id)
        else:
            return HttpResponseForbidden('You cannot start a conversation with this participant for this bid')
    else:
        # If no user specified, determine the other participant automatically
        if request.user.id == bid.user_id:
            # Current user is the bid creator, other participant is the accepted_by
            if bid.accepted_by_id:
                other_participant = bid.accepted_by
            else:
                return HttpResponseForbidden('No one has accepted this bid yet')
        else:
            # Current user is the accepted_by, other participant is the bid creator
            other_participant = bid.user
    
    if not other_participant or other_participant.id == request.user.id:
        return HttpResponseForbidden('Invalid conversation participant')
    
    # Find or create a conversation between these two specific users for this bid
    # Each conversation should have exactly 2 participants
    # Filter conversations that have BOTH users as participants
    conversations = Conversation.objects.filter(
        bid=bid,
        participants=request.user
    ).filter(
        participants=other_participant
    ).annotate(
        participant_count=Count('participants')
    ).filter(
        participant_count=2
    )
    
    # Get the first conversation that has exactly these 2 participants
    conversation = None
    for conv in conversations:
        participants = list(conv.participants.all())
        if len(participants) == 2 and request.user in participants and other_participant in participants:
            conversation = conv
            break
    
    if not conversation:
        conversation = Conversation.objects.create(bid=bid, is_active=True)
        conversation.participants.add(request.user, other_participant)
    else:
        # Reactivate if it was inactive
        if not conversation.is_active:
            conversation.is_active = True
            conversation.save()
        # Ensure both participants are in the conversation
        if request.user not in conversation.participants.all():
            conversation.participants.add(request.user)
        if other_participant not in conversation.participants.all():
            conversation.participants.add(other_participant)
    
    return redirect('messaging:conversation_detail', conversation_id=conversation.id)


@login_required
def start_conversation_for_offer(request, offer_id):
    """Start a new conversation for an offer - creates a 1-on-1 conversation between two users"""
    if not Offer:
        return HttpResponseForbidden('Offers feature not available')
    
    offer = get_object_or_404(Offer, id=offer_id)
    
    # Determine which users are allowed to join a conversation for this offer
    allowed_user_ids = {offer.user_id}
    if offer.accepted_by_id:
        allowed_user_ids.add(offer.accepted_by_id)
    
    # Also allow users who have placed bids on this offer
    if OfferBid:
        bidder_ids = set(
            OfferBid.objects.filter(offer=offer, status__in=['PENDING', 'SELECTED']).values_list('bidder_id', flat=True)
        )
        allowed_user_ids.update(bidder_ids)
    
    if request.user.id not in allowed_user_ids:
        return HttpResponseForbidden('You cannot start a conversation for this offer')
    
    # Determine the other participant
    participant_id = request.GET.get('user')
    other_participant = None
    
    if participant_id:
        try:
            participant_id = int(participant_id)
        except (TypeError, ValueError):
            participant_id = None
        
        if participant_id and participant_id in allowed_user_ids and participant_id != request.user.id:
            other_participant = get_object_or_404(User, id=participant_id)
        else:
            return HttpResponseForbidden('You cannot start a conversation with this participant for this offer')
    else:
        # If no user specified, determine the other participant automatically
        if request.user.id == offer.user_id:
            # Current user is the offer creator, other participant is the accepted_by
            if offer.accepted_by_id:
                other_participant = offer.accepted_by
            else:
                return HttpResponseForbidden('No one has been selected for this offer yet')
        else:
            # Current user is a bidder, other participant is the offer creator
            other_participant = offer.user
    
    if not other_participant or other_participant.id == request.user.id:
        return HttpResponseForbidden('Invalid conversation participant')
    
    # Find or create a conversation between these two specific users for this offer
    # Each conversation should have exactly 2 participants
    # Filter conversations that have BOTH users as participants
    conversations = Conversation.objects.filter(
        offer=offer,
        participants=request.user
    ).filter(
        participants=other_participant
    ).annotate(
        participant_count=Count('participants')
    ).filter(
        participant_count=2
    )
    
    # Get the first conversation that has exactly these 2 participants
    conversation = None
    for conv in conversations:
        participants = list(conv.participants.all())
        if len(participants) == 2 and request.user in participants and other_participant in participants:
            conversation = conv
            break
    
    if not conversation:
        conversation = Conversation.objects.create(offer=offer, is_active=True)
        conversation.participants.add(request.user, other_participant)
    else:
        # Reactivate if it was inactive
        if not conversation.is_active:
            conversation.is_active = True
            conversation.save()
        # Ensure both participants are in the conversation
        if request.user not in conversation.participants.all():
            conversation.participants.add(request.user)
        if other_participant not in conversation.participants.all():
            conversation.participants.add(other_participant)
    
    return redirect('messaging:conversation_detail', conversation_id=conversation.id)


@login_required
@require_http_methods(["POST"])
def send_message(request, conversation_id):
    """Send a message in a conversation"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user,
        is_active=True
    )
    
    form = MessageForm(request.POST)
    if form.is_valid():
        message = form.save(commit=False)
        message.conversation = conversation
        message.sender = request.user
        message.save()
        
        # Update conversation timestamp
        conversation.updated_at = timezone.now()
        conversation.save()
        
        # Send real-time notification (if WebSocket is available)
        try:
            from notifications.utils import send_websocket_notification
            other_participant = conversation.get_other_participant(request.user)
            if other_participant:
                send_websocket_notification(
                    other_participant,
                    {
                        'type': 'new_message',
                        'conversation_id': conversation.id,
                        'message': message.content,
                        'sender': request.user.username,
                        'timestamp': message.created_at.isoformat()
                    }
                )
        except ImportError:
            pass
        
        return JsonResponse({
            'success': True,
            'message': {
                'id': message.id,
                'content': message.content,
                'sender': request.user.username,
                'timestamp': message.created_at.isoformat(),
                'is_read': message.is_read,
                'is_own': True
            }
        })
    
    return JsonResponse({'error': 'Invalid message'}, status=400)


@login_required
@require_http_methods(["GET"])
def get_messages(request, conversation_id):
    """Get messages for a conversation (AJAX)"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user,
        is_active=True
    )
    
    # Get messages
    messages = conversation.messages.select_related('sender').order_by('created_at')
    
    # Pagination
    page = int(request.GET.get('page', 1))
    per_page = 50
    start = (page - 1) * per_page
    end = start + per_page
    
    messages_data = []
    for message in messages[start:end]:
        messages_data.append({
            'id': message.id,
            'content': message.content,
            'sender': message.sender.username,
            'sender_name': f"{message.sender.first_name} {message.sender.last_name}",
            'timestamp': message.created_at.isoformat(),
            'is_read': message.is_read,
            'is_own': message.sender == request.user
        })
    
    return JsonResponse({
        'messages': messages_data,
        'has_more': len(messages) > end
    })


@login_required
@require_http_methods(["POST"])
@csrf_exempt
def typing_indicator(request, conversation_id):
    """Handle typing indicators"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user,
        is_active=True
    )
    
    data = json.loads(request.body)
    is_typing = data.get('is_typing', False)
    
    indicator, created = TypingIndicator.objects.get_or_create(
        conversation=conversation,
        user=request.user,
        defaults={'is_typing': is_typing}
    )
    
    if not created:
        indicator.is_typing = is_typing
        indicator.save()
    
    return JsonResponse({'success': True})


@login_required
@require_http_methods(["GET"])
def get_typing_indicators(request, conversation_id):
    """Get typing indicators for a conversation"""
    conversation = get_object_or_404(
        Conversation,
        id=conversation_id,
        participants=request.user,
        is_active=True
    )
    
    # Get typing indicators (excluding current user)
    indicators = TypingIndicator.objects.filter(
        conversation=conversation,
        is_typing=True
    ).exclude(user=request.user).select_related('user')
    
    typing_users = []
    for indicator in indicators:
        # Check if typing activity is recent (within 3 seconds)
        if (timezone.now() - indicator.last_activity).total_seconds() < 3:
            typing_users.append({
                'username': indicator.user.username,
                'name': f"{indicator.user.first_name} {indicator.user.last_name}"
            })
    
    return JsonResponse({'typing_users': typing_users})


@login_required
def get_unread_message_count(request):
    """Return total unread messages for the current user"""
    count = Message.objects.filter(
        conversation__participants=request.user,
        is_read=False
    ).exclude(sender=request.user).count()
    return JsonResponse({'count': count})