import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from django.utils import timezone
from .models import Conversation, Message, TypingIndicator


class ChatConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time chat"""
    
    async def connect(self):
        """Connect to WebSocket"""
        self.conversation_id = self.scope['url_route']['kwargs']['conversation_id']
        self.room_group_name = f'chat_{self.conversation_id}'
        self.user = self.scope['user']
        
        # Check if user is authenticated and can access this conversation
        if self.user == AnonymousUser():
            await self.close()
            return
        
        # Verify user can access this conversation
        can_access = await self.check_conversation_access()
        if not can_access:
            await self.close()
            return
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send recent messages
        await self.send_recent_messages()
    
    async def disconnect(self, close_code):
        """Disconnect from WebSocket"""
        # Stop typing indicator
        await self.stop_typing()
        
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Receive message from WebSocket"""
        try:
            text_data_json = json.loads(text_data)
            message_type = text_data_json.get('type')
            
            if message_type == 'chat_message':
                await self.handle_chat_message(text_data_json)
            elif message_type == 'typing_start':
                await self.handle_typing_start()
            elif message_type == 'typing_stop':
                await self.handle_typing_stop()
            elif message_type == 'mark_read':
                await self.handle_mark_read(text_data_json)
            
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON'
            }))
    
    async def handle_chat_message(self, data):
        """Handle incoming chat message"""
        content = data.get('content', '').strip()
        
        if not content:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Message cannot be empty'
            }))
            return
        
        # Save message to database
        message = await self.save_message(content)
        
        if message:
            # Send message to room group
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'chat_message',
                    'message': {
                        'id': message.id,
                        'content': message.content,
                        'sender': self.user.username,
                        'sender_name': f"{self.user.first_name} {self.user.last_name}",
                        'timestamp': message.created_at.isoformat(),
                        'is_read': message.is_read,
                        'is_own': False
                    }
                }
            )
    
    async def handle_typing_start(self):
        """Handle typing start indicator"""
        await self.set_typing_indicator(True)
        
        # Send typing indicator to other users
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user': {
                    'username': self.user.username,
                    'name': f"{self.user.first_name} {self.user.last_name}"
                },
                'is_typing': True
            }
        )
    
    async def handle_typing_stop(self):
        """Handle typing stop indicator"""
        await self.set_typing_indicator(False)
        
        # Send typing stop to other users
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'typing_indicator',
                'user': {
                    'username': self.user.username,
                    'name': f"{self.user.first_name} {self.user.last_name}"
                },
                'is_typing': False
            }
        )
    
    async def handle_mark_read(self, data):
        """Handle marking messages as read"""
        message_id = data.get('message_id')
        if message_id:
            await self.mark_message_read(message_id)
    
    async def chat_message(self, event):
        """Send chat message to WebSocket"""
        message = event['message']
        message['is_own'] = message['sender'] == self.user.username
        
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': message
        }))
    
    async def typing_indicator(self, event):
        """Send typing indicator to WebSocket"""
        # Don't send typing indicator to the user who is typing
        if event['user']['username'] != self.user.username:
            await self.send(text_data=json.dumps({
                'type': 'typing_indicator',
                'user': event['user'],
                'is_typing': event['is_typing']
            }))
    
    async def send_recent_messages(self):
        """Send recent messages when connecting"""
        messages = await self.get_recent_messages()
        
        await self.send(text_data=json.dumps({
            'type': 'recent_messages',
            'messages': messages
        }))
    
    @database_sync_to_async
    def check_conversation_access(self):
        """Check if user can access this conversation"""
        try:
            conversation = Conversation.objects.get(
                id=self.conversation_id,
                participants=self.user,
                is_active=True
            )
            return True
        except Conversation.DoesNotExist:
            return False
    
    @database_sync_to_async
    def save_message(self, content):
        """Save message to database"""
        try:
            conversation = Conversation.objects.get(
                id=self.conversation_id,
                participants=self.user,
                is_active=True
            )
            
            message = Message.objects.create(
                conversation=conversation,
                sender=self.user,
                content=content
            )
            
            # Update conversation timestamp
            conversation.updated_at = timezone.now()
            conversation.save()
            
            return message
        except Conversation.DoesNotExist:
            return None
    
    @database_sync_to_async
    def get_recent_messages(self, limit=50):
        """Get recent messages for the conversation"""
        try:
            conversation = Conversation.objects.get(
                id=self.conversation_id,
                participants=self.user,
                is_active=True
            )
            
            messages = conversation.messages.select_related('sender').order_by('-created_at')[:limit]
            
            messages_data = []
            for message in reversed(messages):
                messages_data.append({
                    'id': message.id,
                    'content': message.content,
                    'sender': message.sender.username,
                    'sender_name': f"{message.sender.first_name} {message.sender.last_name}",
                    'timestamp': message.created_at.isoformat(),
                    'is_read': message.is_read,
                    'is_own': message.sender == self.user
                })
            
            return messages_data
        except Conversation.DoesNotExist:
            return []
    
    @database_sync_to_async
    def set_typing_indicator(self, is_typing):
        """Set typing indicator"""
        try:
            conversation = Conversation.objects.get(
                id=self.conversation_id,
                participants=self.user,
                is_active=True
            )
            
            indicator, created = TypingIndicator.objects.get_or_create(
                conversation=conversation,
                user=self.user,
                defaults={'is_typing': is_typing}
            )
            
            if not created:
                indicator.is_typing = is_typing
                indicator.save()
        except Conversation.DoesNotExist:
            pass
    
    @database_sync_to_async
    def stop_typing(self):
        """Stop typing indicator"""
        try:
            conversation = Conversation.objects.get(
                id=self.conversation_id,
                participants=self.user,
                is_active=True
            )
            
            TypingIndicator.objects.filter(
                conversation=conversation,
                user=self.user
            ).update(is_typing=False)
        except Conversation.DoesNotExist:
            pass
    
    @database_sync_to_async
    def mark_message_read(self, message_id):
        """Mark a message as read"""
        try:
            message = Message.objects.filter(
                id=message_id,
                conversation__participants=self.user
            ).exclude(sender=self.user).first()
            if message:
                message.mark_as_read()
        except Message.DoesNotExist:
            pass
