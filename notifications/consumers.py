import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from .models import Notification


class NotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time notifications"""
    
    async def connect(self):
        """Connect to WebSocket"""
        self.user_id = self.scope['url_route']['kwargs']['user_id']
        self.room_group_name = f'notifications_{self.user_id}'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Disconnect from WebSocket"""
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
            
            if message_type == 'mark_read':
                notification_id = text_data_json.get('notification_id')
                await self.mark_notification_read(notification_id)
            
        except json.JSONDecodeError:
            pass
    
    async def notification_message(self, event):
        """Send notification to WebSocket"""
        message = event['message']
        
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'message': message,
            'title': event.get('title', 'New Notification'),
            'notification_type': event.get('notification_type', 'SYSTEM_ANNOUNCEMENT'),
            'timestamp': event.get('timestamp'),
        }))
    
    async def bid_update(self, event):
        """Send bid update notification"""
        await self.send(text_data=json.dumps({
            'type': 'bid_update',
            'message': event['message'],
            'bid_id': event.get('bid_id'),
            'status': event.get('status'),
        }))
    
    async def new_message(self, event):
        """Send new message notification"""
        await self.send(text_data=json.dumps({
            'type': 'new_message',
            'message': event['message'],
            'sender': event.get('sender'),
            'bid_id': event.get('bid_id'),
        }))
    
    async def payment_update(self, event):
        """Send payment update notification"""
        await self.send(text_data=json.dumps({
            'type': 'payment_update',
            'message': event['message'],
            'amount': event.get('amount'),
            'transaction_type': event.get('transaction_type'),
        }))
    
    @database_sync_to_async
    def mark_notification_read(self, notification_id):
        """Mark notification as read"""
        try:
            notification = Notification.objects.get(
                id=notification_id,
                user_id=self.user_id
            )
            notification.mark_as_read()
        except Notification.DoesNotExist:
            pass


class AdminNotificationConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for admin notifications"""
    
    async def connect(self):
        """Connect to admin WebSocket"""
        self.room_group_name = 'admin_notifications'
        
        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
    
    async def disconnect(self, close_code):
        """Disconnect from WebSocket"""
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )
    
    async def admin_notification(self, event):
        """Send admin notification"""
        await self.send(text_data=json.dumps({
            'type': 'admin_notification',
            'message': event['message'],
            'notification_type': event.get('notification_type', 'SYSTEM'),
            'timestamp': event.get('timestamp'),
        }))
    
    async def metrics_update(self, event):
        """Send metrics update"""
        await self.send(text_data=json.dumps({
            'type': 'metrics_update',
            'metrics': event['metrics'],
            'timestamp': event.get('timestamp'),
        }))
