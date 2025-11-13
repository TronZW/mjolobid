from django.urls import path
from . import views

app_name = 'messaging'

urlpatterns = [
    path('', views.conversation_list, name='conversation_list'),
    path('conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('start/<int:bid_id>/', views.start_conversation, name='start_conversation'),
    path('start-offer/<int:offer_id>/', views.start_conversation_for_offer, name='start_conversation_for_offer'),
    path('send/<int:conversation_id>/', views.send_message, name='send_message'),
    path('messages/<int:conversation_id>/', views.get_messages, name='get_messages'),
    path('typing/<int:conversation_id>/', views.typing_indicator, name='typing_indicator'),
    path('typing-status/<int:conversation_id>/', views.get_typing_indicators, name='get_typing_indicators'),
    path('api/unread-count/', views.get_unread_message_count, name='unread_count'),
]
