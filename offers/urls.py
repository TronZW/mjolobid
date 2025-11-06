from django.urls import path
from . import views

app_name = 'offers'

urlpatterns = [
    path('', views.browse_offers, name='browse_offers'),
    path('create/', views.create_offer, name='create_offer'),
    path('my-offers/', views.my_offers, name='my_offers'),
    path('my-bids/', views.my_offer_bids, name='my_offer_bids'),
    path('offer/<int:offer_id>/', views.offer_detail, name='offer_detail'),
    path('offer/<int:offer_id>/edit/', views.edit_offer, name='edit_offer'),
    path('offer/<int:offer_id>/delete/', views.delete_offer, name='delete_offer'),
    path('offer/<int:offer_id>/bids/', views.view_offer_bids, name='view_offer_bids'),
    path('offer/<int:offer_id>/bid/', views.place_bid_on_offer, name='place_bid'),
    path('offer/<int:offer_id>/choose/<int:bid_id>/', views.choose_bid, name='choose_bid'),
]

