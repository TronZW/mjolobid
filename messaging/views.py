from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db.models import Q, Prefetch
from django.core.paginator import Paginator
import json

from .models import Conversation, Message, MessageAttachment, TypingIndicator
from .forms import MessageForm
from bids.models import Bid


@login_required
def conversation_list(request):
    """List all conversations for the current user"""
    conversations = Conversation.objects.filter(
        participants=request.user,
        is_active=True
    ).select_related('bid', 'bid__user', 'bid__accepted_by').prefetch_related(
        Prefetch('messages', queryset=Message.objects.select_related('sender').order_by('-created_at')[:1])
    ).order_by('-updated_at')
    
    # Add unread counts
    for conversation in conversations:
        conversation.unread_count = conversation.get_unread_count(request.user)
        conversation.other_participant = conversation.get_other_participant(request.user)
        conversation.latest_message = conversation.get_latest_message()
    
    context = {
        'conversations': conversations,
    }
    return render(request, 'messaging/conversation_list.html', context)


@login_required
def conversation_detail(request, conversation_id):
    """View individual conversation"""
    conversation = get_object_or_404(
        Conversation.objects.select_related('bid', 'bid__user', 'bid__accepted_by'),
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
    """Start a new conversation for a bid"""
    bid = get_object_or_404(Bid, id=bid_id)
    
    # Check if user can start conversation
    if request.user not in [bid.user, bid.accepted_by]:
        return JsonResponse({'error': 'You cannot start a conversation for this bid'}, status=403)
    
    # Check if conversation already exists
    conversation, created = Conversation.objects.get_or_create(
        bid=bid,
        defaults={'is_active': True}
    )
    
    # Add participants if not already added
    if request.user not in conversation.participants.all():
        conversation.participants.add(request.user)
    if bid.user not in conversation.participants.all():
        conversation.participants.add(bid.user)
    if bid.accepted_by and bid.accepted_by not in conversation.participants.all():
        conversation.participants.add(bid.accepted_by)
    
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
                'is_read': message.is_read
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