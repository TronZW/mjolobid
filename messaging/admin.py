from django.contrib import admin
from .models import Conversation, Message, MessageAttachment, TypingIndicator


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ['id', 'bid', 'created_at', 'updated_at', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['bid__title', 'participants__username']
    readonly_fields = ['created_at', 'updated_at']
    
    def get_participants(self, obj):
        return ", ".join([p.username for p in obj.participants.all()])
    get_participants.short_description = 'Participants'


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'sender', 'content_preview', 'is_read', 'created_at']
    list_filter = ['is_read', 'created_at']
    search_fields = ['content', 'sender__username', 'conversation__bid__title']
    readonly_fields = ['created_at', 'read_at']
    
    def content_preview(self, obj):
        return obj.content[:50] + "..." if len(obj.content) > 50 else obj.content
    content_preview.short_description = 'Content Preview'


@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    list_display = ['id', 'message', 'filename', 'file_size', 'content_type', 'created_at']
    list_filter = ['content_type', 'created_at']
    search_fields = ['filename', 'message__content']


@admin.register(TypingIndicator)
class TypingIndicatorAdmin(admin.ModelAdmin):
    list_display = ['id', 'conversation', 'user', 'is_typing', 'last_activity']
    list_filter = ['is_typing', 'last_activity']
    search_fields = ['user__username', 'conversation__bid__title']