from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from bids.models import Bid

User = get_user_model()


class Conversation(models.Model):
    """Chat conversation between two users"""
    
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE, related_name='conversations', null=True, blank=True)
    offer = models.ForeignKey('offers.Offer', on_delete=models.CASCADE, related_name='conversations', null=True, blank=True)
    participants = models.ManyToManyField(User, related_name='conversations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        ordering = ['-updated_at']
        unique_together = [['bid'], ['offer']]
    
    def __str__(self):
        if self.bid:
            return f"Conversation for {self.bid.title}"
        elif self.offer:
            return f"Conversation for {self.offer.title}"
        return "Conversation"
    
    def get_title(self):
        """Get the title of the related bid or offer"""
        if self.bid:
            return self.bid.title
        elif self.offer:
            return self.offer.title
        return "Conversation"
    
    def get_other_participant(self, user):
        """Get the other participant in the conversation"""
        return self.participants.exclude(id=user.id).first()
    
    def get_latest_message(self):
        """Get the latest message in the conversation"""
        return self.messages.first()
    
    def get_unread_count(self, user):
        """Get unread message count for a user"""
        return self.messages.exclude(
            sender=user
        ).filter(
            is_read=False
        ).count()


class Message(models.Model):
    """Individual message in a conversation"""
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField(max_length=2000)
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        title = self.conversation.get_title()
        return f"Message from {self.sender.username} in {title}"
    
    def mark_as_read(self):
        """Mark message as read"""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


class MessageAttachment(models.Model):
    """File attachments for messages"""
    
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='message_attachments/')
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    content_type = models.CharField(max_length=100)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Attachment: {self.filename}"


class TypingIndicator(models.Model):
    """Track who is typing in a conversation"""
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='typing_indicators')
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    is_typing = models.BooleanField(default=False)
    last_activity = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['conversation', 'user']
    
    def __str__(self):
        title = self.conversation.get_title()
        return f"{self.user.username} typing in {title}"