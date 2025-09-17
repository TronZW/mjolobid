#!/usr/bin/env python
"""
Quick data seeding script for MjoloBid.
Creates essential dummy data for testing and demo purposes.
"""

import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal
import random

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mjolobid.settings_render')

# Setup Django
django.setup()

from django.contrib.auth import get_user_model
from bids.models import EventCategory, Bid

User = get_user_model()

def create_essential_data():
    """Create essential dummy data"""
    print("🌱 Creating essential dummy data...")
    
    # Create event categories
    categories_data = [
        {"name": "Club Night", "icon": "🕺", "description": "Nightclub events and parties"},
        {"name": "Concert", "icon": "🎵", "description": "Music concerts and live performances"},
        {"name": "Restaurant", "icon": "🍽️", "description": "Dining out and restaurant visits"},
        {"name": "Movie", "icon": "🎬", "description": "Cinema and movie outings"},
    ]
    
    for cat_data in categories_data:
        category, created = EventCategory.objects.get_or_create(
            name=cat_data["name"],
            defaults=cat_data
        )
        if created:
            print(f"  ✅ Created category: {category.name}")
    
    # Create a few test users
    test_users = [
        {"username": "test_male", "email": "male@test.com", "gender": "M", "user_type": "M", "first_name": "Tendai", "phone": "0771234567"},
        {"username": "test_female", "email": "female@test.com", "gender": "F", "user_type": "F", "first_name": "Rutendo", "phone": "0777654321"},
    ]
    
    for user_data in test_users:
        if not User.objects.filter(username=user_data["username"]).exists():
            user = User.objects.create_user(
                username=user_data["username"],
                email=user_data["email"],
                password="password123",
                first_name=user_data["first_name"],
                last_name="Test",
                gender=user_data["gender"],
                user_type=user_data["user_type"],
                phone_number=user_data["phone"],
                city="Harare",
                bio="Test user for demo purposes"
            )
            print(f"  ✅ Created user: {user.username}")
    
    # Create a few test bids
    male_user = User.objects.filter(user_type="M").first()
    if male_user and EventCategory.objects.exists():
        category = EventCategory.objects.first()
        
        test_bids = [
            {
                "title": "Looking for company to Club 7 tonight",
                "description": "Great night out planned! Let's have fun together.",
                "bid_amount": Decimal("150.00"),
                "event_date": datetime.now() + timedelta(days=1, hours=20)
            },
            {
                "title": "Need a date for the Jazz Festival",
                "description": "Amazing music event this weekend. Perfect for music lovers!",
                "bid_amount": Decimal("200.00"),
                "event_date": datetime.now() + timedelta(days=3, hours=19)
            }
        ]
        
        for bid_data in test_bids:
            if not Bid.objects.filter(title=bid_data["title"]).exists():
                bid = Bid.objects.create(
                    user=male_user,
                    title=bid_data["title"],
                    description=bid_data["description"],
                    event_category=category,
                    event_date=bid_data["event_date"],
                    event_location="Harare, Zimbabwe",
                    event_address="123 Main Street, Harare",
                    bid_amount=bid_data["bid_amount"],
                    commission_amount=bid_data["bid_amount"] * Decimal("0.15")
                )
                print(f"  ✅ Created bid: {bid.title}")
    
    print("✅ Essential data creation completed!")

if __name__ == "__main__":
    create_essential_data()
