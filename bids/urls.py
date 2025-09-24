from django.urls import path
from . import views

app_name = 'bids'

urlpatterns = [
    path('', views.browse_bids, name='browse_bids'),
    path('events/', views.upcoming_events, name='upcoming_events'),
    path('events/add/', views.add_event, name='add_event'),
    path('events/<int:event_id>/bid/', views.post_bid_for_event, name='post_bid_for_event'),
    path('male-home/', views.male_homepage, name='male_homepage'),
    path('bid/<int:bid_id>/', views.bid_detail, name='bid_detail'),
    path('bid/<int:bid_id>/edit/', views.edit_bid, name='edit_bid'),
    path('accept/<int:bid_id>/', views.accept_bid, name='accept_bid'),
    path('my-bids/', views.my_bids, name='my_bids'),
    path('post-bid/', views.post_bid, name='post_bid'),
    path('accepted-bids/', views.my_accepted_bids, name='my_accepted_bids'),
    path('complete/<int:bid_id>/', views.complete_bid, name='complete_bid'),
    path('review/<int:bid_id>/', views.review_bid, name='review_bid'),
    path('boost/<int:bid_id>/', views.boost_bid, name='boost_bid'),
]
