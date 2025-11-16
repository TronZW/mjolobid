"""
Management command to separate conversations that have more than 2 participants
into individual 1-on-1 conversations.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from messaging.models import Conversation, Message
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Separate conversations with multiple participants into 1-on-1 conversations'

    def handle(self, *args, **options):
        self.stdout.write('Starting conversation separation...')
        
        # Find all conversations with more than 2 participants
        conversations_to_fix = []
        for conv in Conversation.objects.all():
            participant_count = conv.participants.count()
            if participant_count > 2:
                conversations_to_fix.append(conv)
        
        self.stdout.write(f'Found {len(conversations_to_fix)} conversations with more than 2 participants')
        
        separated_count = 0
        
        with transaction.atomic():
            for conv in conversations_to_fix:
                participants = list(conv.participants.all())
                
                if len(participants) < 2:
                    continue
                
                # Get the primary user (bid/offer creator)
                primary_user = None
                if conv.bid:
                    primary_user = conv.bid.user
                elif conv.offer:
                    primary_user = conv.offer.user
                
                if not primary_user:
                    continue
                
                # Get all messages for this conversation
                messages = list(conv.messages.all().order_by('created_at'))
                
                # Create separate conversations for each other participant
                other_participants = [p for p in participants if p != primary_user]
                
                for other_user in other_participants:
                    # Check if a 1-on-1 conversation already exists
                    existing_convs = Conversation.objects.filter(
                        bid=conv.bid if conv.bid else None,
                        offer=conv.offer if conv.offer else None,
                        participants=primary_user
                    ).filter(
                        participants=other_user
                    ).annotate(
                        participant_count=Count('participants')
                    )
                    
                    existing_conv = None
                    for ec in existing_convs:
                        ec_participants = list(ec.participants.all())
                        if len(ec_participants) == 2 and primary_user in ec_participants and other_user in ec_participants:
                            existing_conv = ec
                            break
                    
                    if existing_conv:
                        # Copy messages between these two users to the existing conversation
                        user_messages = [m for m in messages if m.sender in [primary_user, other_user]]
                        for msg in user_messages:
                            # Check if message is already in the existing conversation
                            if not existing_conv.messages.filter(id=msg.id).exists():
                                # Create a copy of the message for the new conversation
                                Message.objects.create(
                                    conversation=existing_conv,
                                    sender=msg.sender,
                                    content=msg.content,
                                    is_read=msg.is_read,
                                    read_at=msg.read_at,
                                    created_at=msg.created_at
                                )
                        if user_messages:
                            existing_conv.updated_at = max([m.created_at for m in user_messages])
                            existing_conv.save()
                    else:
                        # Create new 1-on-1 conversation
                        new_conv = Conversation.objects.create(
                            bid=conv.bid,
                            offer=conv.offer,
                            is_active=conv.is_active,
                            created_at=conv.created_at,
                            updated_at=conv.updated_at
                        )
                        new_conv.participants.add(primary_user, other_user)
                        
                        # Copy messages between these two users to the new conversation
                        user_messages = [m for m in messages if m.sender in [primary_user, other_user]]
                        for msg in user_messages:
                            Message.objects.create(
                                conversation=new_conv,
                                sender=msg.sender,
                                content=msg.content,
                                is_read=msg.is_read,
                                read_at=msg.read_at,
                                created_at=msg.created_at
                            )
                        
                        if user_messages:
                            new_conv.updated_at = max([m.created_at for m in user_messages])
                            new_conv.save()
                        
                        separated_count += 1
                        self.stdout.write(f'Created new conversation between {primary_user.username} and {other_user.username} with {len(user_messages)} messages')
                
                # Delete the old conversation if it has no more messages
                if conv.messages.count() == 0:
                    conv.delete()
                    self.stdout.write(f'Deleted old conversation {conv.id}')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully separated {separated_count} conversations'))

