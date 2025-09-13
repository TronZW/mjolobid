from django.urls import path
from . import views

app_name = 'bids'

urlpatterns = [
    path('', views.browse_bids, name='browse_bids'),
    path('bid/<int:bid_id>/', views.bid_detail, name='bid_detail'),
    path('accept/<int:bid_id>/', views.accept_bid, name='accept_bid'),
    path('my-bids/', views.my_bids, name='my_bids'),
    path('post-bid/', views.post_bid, name='post_bid'),
    path('accepted-bids/', views.my_accepted_bids, name='my_accepted_bids'),
    path('message/<int:bid_id>/', views.send_message, name='send_message'),
    path('complete/<int:bid_id>/', views.complete_bid, name='complete_bid'),
    path('review/<int:bid_id>/', views.review_bid, name='review_bid'),
    path('boost/<int:bid_id>/', views.boost_bid, name='boost_bid'),
]
