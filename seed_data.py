#!/usr/bin/env python
"""
Comprehensive data seeding script for MjoloBid.
Creates dummy users, bids, categories, and other sample data.
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
from accounts.models import UserProfile, UserRating
from bids.models import EventCategory, Bid, BidImage, BidMessage
from payments.models import Transaction, PaymentMethod

User = get_user_model()

# Sample data
MALE_NAMES = [
    "Tendai", "Tafadzwa", "Blessing", "Tinashe", "Kudakwashe", "Tatenda", "Tawanda", "Farai",
    "Munyaradzi", "Tonderai", "Tapiwa", "Rumbidzai", "Tarisai", "Tendekai", "Tawanda", "Tafara"
]

FEMALE_NAMES = [
    "Rumbidzai", "Tarisai", "Tendekai", "Rutendo", "Rumbidzai", "Tarisai", "Tendekai", "Rutendo",
    "Rumbidzai", "Tarisai", "Tendekai", "Rutendo", "Rumbidzai", "Tarisai", "Tendekai", "Rutendo"
]

CITIES = ["Harare", "Bulawayo", "Gweru", "Mutare", "Kwekwe", "Kadoma", "Chitungwiza", "Masvingo"]

EVENT_CATEGORIES = [
    {"name": "Club Night", "icon": "🕺", "description": "Nightclub events and parties"},
    {"name": "Concert", "icon": "🎵", "description": "Music concerts and live performances"},
    {"name": "Restaurant", "icon": "🍽️", "description": "Dining out and restaurant visits"},
    {"name": "Movie", "icon": "🎬", "description": "Cinema and movie outings"},
    {"name": "Sports Event", "icon": "⚽", "description": "Sports games and events"},
    {"name": "Festival", "icon": "🎪", "description": "Cultural festivals and celebrations"},
    {"name": "Beach", "icon": "🏖️", "description": "Beach outings and water activities"},
    {"name": "Shopping", "icon": "🛍️", "description": "Shopping trips and mall visits"},
]

EVENT_LOCATIONS = [
    "Sam Levy's Village, Borrowdale", "Avondale Shopping Centre", "Eastgate Mall", "Westgate Mall",
    "Hippo Valley Estates", "Chapungu Sculpture Park", "Mukuvisi Woodlands", "Harare Gardens",
    "National Gallery of Zimbabwe", "Reps Theatre", "7 Arts Theatre", "Book Cafe",
    "Monomotapa Hotel", "Meikles Hotel", "Rainbow Towers", "Cresta Lodge"
]

def create_event_categories():
    """Create event categories"""
    print("📂 Creating event categories...")
    
    for category_data in EVENT_CATEGORIES:
        category, created = EventCategory.objects.get_or_create(
            name=category_data["name"],
            defaults={
                "icon": category_data["icon"],
                "description": category_data["description"],
                "is_active": True
            }
        )
        if created:
            print(f"  ✅ Created category: {category.name}")
        else:
            print(f"  ⚠️  Category already exists: {category.name}")

def create_dummy_users():
    """Create dummy users"""
    print("👥 Creating dummy users...")
    
    # Create male users (bidders)
    for i, name in enumerate(MALE_NAMES[:8]):
        username = f"male_user_{i+1}"
        email = f"{username}@example.com"
        phone = f"077{random.randint(1000000, 9999999)}"
        
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                email=email,
                password="password123",
                first_name=name,
                last_name="Moyo",
                gender="M",
                user_type="M",
                phone_number=phone,
                city=random.choice(CITIES),
                bio=f"Hi! I'm {name}, looking for fun social experiences in {random.choice(CITIES)}. Let's have a great time together!",
                is_verified=random.choice([True, False]),
                wallet_balance=Decimal(random.randint(50, 500)),
                date_of_birth=datetime.now().date() - timedelta(days=random.randint(6570, 14600))  # 18-40 years old
            )
            print(f"  ✅ Created male user: {user.username}")
        else:
            print(f"  ⚠️  Male user already exists: {username}")
    
    # Create female users (acceptors)
    for i, name in enumerate(FEMALE_NAMES[:8]):
        username = f"female_user_{i+1}"
        email = f"{username}@example.com"
        phone = f"077{random.randint(1000000, 9999999)}"
        
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_user(
                username=username,
                email=email,
                password="password123",
                first_name=name,
                last_name="Moyo",
                gender="F",
                user_type="F",
                phone_number=phone,
                city=random.choice(CITIES),
                bio=f"Hi! I'm {name}, excited to meet new people and have amazing experiences. Let's create memories together!",
                is_verified=random.choice([True, False]),
                wallet_balance=Decimal(random.randint(20, 200)),
                date_of_birth=datetime.now().date() - timedelta(days=random.randint(6570, 14600))  # 18-40 years old
            )
            print(f"  ✅ Created female user: {user.username}")
        else:
            print(f"  ⚠️  Female user already exists: {username}")

def create_dummy_bids():
    """Create dummy bids"""
    print("💰 Creating dummy bids...")
    
    male_users = User.objects.filter(user_type="M")
    categories = EventCategory.objects.all()
    
    if not male_users.exists() or not categories.exists():
        print("  ❌ No male users or categories found. Please create users and categories first.")
        return
    
    bid_titles = [
        "Looking for company to Club 7 tonight",
        "Need a date for the Jazz Festival",
        "Want to go to the new restaurant in Borrowdale",
        "Looking for someone to watch the new Marvel movie",
        "Need company for the football match this weekend",
        "Want to attend the cultural festival together",
        "Looking for a beach day companion",
        "Need someone to go shopping with me",
        "Want to try the new club in Avondale",
        "Looking for company for the art exhibition"
    ]
    
    bid_descriptions = [
        "I'm looking for someone fun and outgoing to join me for a great night out. We'll have drinks, dance, and make memories!",
        "This event promises to be amazing and I'd love to share the experience with someone special. Let's have a wonderful time together!",
        "I've heard great things about this place and would love to try it with good company. Great food and great conversation guaranteed!",
        "The new movie looks fantastic and I'd love to watch it with someone who appreciates good cinema. Popcorn and fun included!",
        "The match is going to be exciting and I'd love to share the energy with someone who enjoys sports as much as I do!",
        "This festival celebrates our beautiful culture and I'd love to experience it with someone who appreciates tradition and fun!",
        "Perfect weather for a beach day! Let's enjoy the sun, sand, and maybe some water activities. Great way to relax and have fun!",
        "I need to do some shopping and would love company. We can browse, try things on, and maybe grab a coffee break!",
        "This new club has amazing vibes and I'd love to check it out with someone who knows how to have a good time!",
        "The art exhibition features some incredible local artists. Perfect for someone who appreciates creativity and culture!"
    ]
    
    for i in range(15):  # Create 15 bids
        user = random.choice(male_users)
        category = random.choice(categories)
        title = random.choice(bid_titles)
        description = random.choice(bid_descriptions)
        
        # Create bid with future event date
        event_date = datetime.now() + timedelta(days=random.randint(1, 30), hours=random.randint(18, 23))
        bid_amount = Decimal(random.randint(50, 300))
        commission = bid_amount * Decimal('0.15')  # 15% commission
        
        bid = Bid.objects.create(
            user=user,
            title=title,
            description=description,
            event_category=category,
            event_date=event_date,
            event_location=random.choice(EVENT_LOCATIONS),
            event_address=f"{random.choice(EVENT_LOCATIONS)}, {random.choice(CITIES)}",
            bid_amount=bid_amount,
            commission_amount=commission,
            status="PENDING",
            latitude=Decimal('-17.8252') + Decimal(str(random.uniform(-0.1, 0.1))),
            longitude=Decimal('31.0335') + Decimal(str(random.uniform(-0.1, 0.1)))
        )
        print(f"  ✅ Created bid: {bid.title} by {bid.user.username}")

def create_accepted_bids():
    """Create some accepted bids"""
    print("🤝 Creating accepted bids...")
    
    pending_bids = Bid.objects.filter(status="PENDING")
    female_users = User.objects.filter(user_type="F")
    
    if not pending_bids.exists() or not female_users.exists():
        print("  ❌ No pending bids or female users found.")
        return
    
    # Accept some bids
    bids_to_accept = random.sample(list(pending_bids), min(5, len(pending_bids)))
    
    for bid in bids_to_accept:
        acceptor = random.choice(female_users)
        bid.accepted_by = acceptor
        bid.accepted_at = datetime.now()
        bid.status = "ACCEPTED"
        bid.save()
        
        print(f"  ✅ Accepted bid: {bid.title} by {acceptor.username}")

def create_user_ratings():
    """Create some user ratings"""
    print("⭐ Creating user ratings...")
    
    accepted_bids = Bid.objects.filter(status="ACCEPTED")
    
    for bid in accepted_bids[:3]:  # Rate first 3 accepted bids
        # Create rating from acceptor to bidder
        rating = UserRating.objects.create(
            rater=bid.accepted_by,
            rated_user=bid.user,
            rating=random.randint(4, 5),
            comment=random.choice([
                "Great company! Had an amazing time.",
                "Very respectful and fun to be around.",
                "Excellent communication and planning.",
                "Made the event so much more enjoyable!",
                "Highly recommend - great personality!"
            ]),
            bid=bid
        )
        print(f"  ✅ Created rating: {rating.rating}/5 stars from {rating.rater.username} to {rating.rated_user.username}")

def create_transactions():
    """Create some sample transactions"""
    print("💳 Creating sample transactions...")
    
    accepted_bids = Bid.objects.filter(status="ACCEPTED")
    
    for bid in accepted_bids[:3]:  # Create transactions for first 3 accepted bids
        # Create payment transaction
        transaction = Transaction.objects.create(
            user=bid.user,
            amount=bid.bid_amount,
            transaction_type="PAYMENT",
            status="COMPLETED",
            description=f"Payment for bid: {bid.title}",
            reference=f"BID_{bid.id}_{random.randint(1000, 9999)}"
        )
        print(f"  ✅ Created transaction: ${transaction.amount} for {transaction.user.username}")

def main():
    """Main seeding function"""
    print("🌱 Starting MjoloBid data seeding...")
    print("=" * 50)
    
    try:
        # Create categories first
        create_event_categories()
        print()
        
        # Create users
        create_dummy_users()
        print()
        
        # Create bids
        create_dummy_bids()
        print()
        
        # Create accepted bids
        create_accepted_bids()
        print()
        
        # Create ratings
        create_user_ratings()
        print()
        
        # Create transactions
        create_transactions()
        print()
        
        print("🎉 Data seeding completed successfully!")
        print("=" * 50)
        print("📊 Summary:")
        print(f"  👥 Users: {User.objects.count()}")
        print(f"  📂 Categories: {EventCategory.objects.count()}")
        print(f"  💰 Bids: {Bid.objects.count()}")
        print(f"  🤝 Accepted Bids: {Bid.objects.filter(status='ACCEPTED').count()}")
        print(f"  ⭐ Ratings: {UserRating.objects.count()}")
        print(f"  💳 Transactions: {Transaction.objects.count()}")
        
    except Exception as e:
        print(f"❌ Error during seeding: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
