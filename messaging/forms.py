from django import forms
from .models import Message, MessageAttachment


class MessageForm(forms.ModelForm):
    """Form for sending messages"""
    
    class Meta:
        model = Message
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-primary focus:border-transparent resize-none',
                'placeholder': 'Type your message...',
                'rows': 3,
                'maxlength': 2000
            })
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['content'].required = True
        self.fields['content'].label = ''


class MessageWithAttachmentForm(MessageForm):
    """Form for sending messages with file attachments"""
    
    attachment = forms.FileField(
        required=False,
        widget=forms.FileInput(attrs={
            'class': 'hidden',
            'accept': 'image/*,.pdf,.doc,.docx,.txt'
        })
    )
    
    class Meta(MessageForm.Meta):
        fields = ['content', 'attachment']
    
    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            # Check file size (max 10MB)
            if attachment.size > 10 * 1024 * 1024:
                raise forms.ValidationError('File size cannot exceed 10MB')
            
            # Check file type
            allowed_types = [
                'image/jpeg', 'image/png', 'image/gif', 'image/webp',
                'application/pdf',
                'application/msword',
                'application/vnd.openxmlformats-officedocument.wordprocessingml.document',
                'text/plain'
            ]
            if attachment.content_type not in allowed_types:
                raise forms.ValidationError('File type not allowed')
        
        return attachment
