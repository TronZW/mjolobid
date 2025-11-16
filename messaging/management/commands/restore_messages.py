"""
Management command to restore messages that might be in conversations that aren't showing up.
This will ensure all messages are in proper 1-on-1 conversations.
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from django.db.models import Count
from messaging.models import Conversation, Message
from django.contrib.auth import get_user_model

User = get_user_model()


class Command(BaseCommand):
    help = 'Restore messages by ensuring they are in proper 1-on-1 conversations'

    def handle(self, *args, **options):
        self.stdout.write('Starting message restoration...')
        
        # Get all messages
        all_messages = Message.objects.select_related('conversation', 'sender').all()
        self.stdout.write(f'Found {all_messages.count()} total messages')
        
        restored_count = 0
        created_count = 0
        
        with transaction.atomic():
            for message in all_messages:
                conv = message.conversation
                if not conv:
                    self.stdout.write(self.style.WARNING(f'Message {message.id} has no conversation!'))
                    continue
                
                participants = list(conv.participants.all())
                
                # If conversation has exactly 2 participants, it's fine
                if len(participants) == 2:
                    continue
                
                # If conversation has more than 2 participants, we need to create separate conversations
                if len(participants) > 2:
                    # Get the primary user (bid/offer creator)
                    primary_user = None
                    if conv.bid:
                        primary_user = conv.bid.user
                    elif conv.offer:
                        primary_user = conv.offer.user
                    
                    if not primary_user:
                        continue
                    
                    # Determine the other participant for this message
                    # If message sender is primary_user, other participant is the recipient
                    # If message sender is not primary_user, other participant is primary_user
                    if message.sender == primary_user:
                        # Find who this message was meant for (check other participants)
                        other_participants = [p for p in participants if p != primary_user]
                        if other_participants:
                            # For now, assign to first other participant
                            # In a real scenario, we'd need more context
                            other_user = other_participants[0]
                        else:
                            continue
                    else:
                        other_user = message.sender
                    
                    # Find or create a 1-on-1 conversation
                    existing_convs = Conversation.objects.filter(
                        bid=conv.bid if conv.bid else None,
                        offer=conv.offer if conv.offer else None,
                        participants=primary_user
                    ).filter(
                        participants=other_user
                    )
                    
                    target_conv = None
                    for ec in existing_convs:
                        ec_participants = list(ec.participants.all())
                        if len(ec_participants) == 2 and primary_user in ec_participants and other_user in ec_participants:
                            target_conv = ec
                            break
                    
                    if not target_conv:
                        # Create new 1-on-1 conversation
                        target_conv = Conversation.objects.create(
                            bid=conv.bid,
                            offer=conv.offer,
                            is_active=True,
                            created_at=conv.created_at,
                            updated_at=message.created_at
                        )
                        target_conv.participants.add(primary_user, other_user)
                        created_count += 1
                        self.stdout.write(f'Created conversation {target_conv.id} between {primary_user.username} and {other_user.username}')
                    
                    # Move message to the target conversation
                    if message.conversation != target_conv:
                        message.conversation = target_conv
                        message.save()
                        restored_count += 1
                
                # If conversation has less than 2 participants, try to fix it
                elif len(participants) < 2:
                    # Try to determine the other participant from the message sender
                    if message.sender not in participants:
                        conv.participants.add(message.sender)
                        self.stdout.write(f'Added {message.sender.username} to conversation {conv.id}')
                    
                    # If still less than 2, try to get from bid/offer
                    if conv.participants.count() < 2:
                        if conv.bid:
                            if conv.bid.user not in participants:
                                conv.participants.add(conv.bid.user)
                        elif conv.offer:
                            if conv.offer.user not in participants:
                                conv.participants.add(conv.offer.user)
        
        self.stdout.write(self.style.SUCCESS(f'Restored {restored_count} messages to proper conversations'))
        self.stdout.write(self.style.SUCCESS(f'Created {created_count} new conversations'))

