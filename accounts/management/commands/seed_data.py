from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import datetime, timedelta
from decimal import Decimal
import random

from bids.models import EventCategory, Bid

User = get_user_model()

class Command(BaseCommand):
    help = 'Seed the database with dummy data'

    def handle(self, *args, **options):
        self.stdout.write("🌱 Starting data seeding...")
        
        try:
            # Create event categories
            self.create_categories()
            
            # Create users
            self.create_users()
            
            # Create bids
            self.create_bids()
            
            self.stdout.write(
                self.style.SUCCESS('✅ Data seeding completed successfully!')
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error during seeding: {e}')
            )
            import traceback
            traceback.print_exc()

    def create_categories(self):
        """Create event categories"""
        self.stdout.write("📂 Creating event categories...")
        
        categories_data = [
            {"name": "Club Night", "icon": "🕺", "description": "Nightclub events and parties"},
            {"name": "Concert", "icon": "🎵", "description": "Music concerts and live performances"},
            {"name": "Restaurant", "icon": "🍽️", "description": "Dining out and restaurant visits"},
            {"name": "Movie", "icon": "🎬", "description": "Cinema and movie outings"},
            {"name": "Sports Event", "icon": "⚽", "description": "Sports games and events"},
        ]
        
        for cat_data in categories_data:
            category, created = EventCategory.objects.get_or_create(
                name=cat_data["name"],
                defaults=cat_data
            )
            if created:
                self.stdout.write(f"  ✅ Created category: {category.name}")

    def create_users(self):
        """Create dummy users"""
        self.stdout.write("👥 Creating dummy users...")
        
        # Create male users (bidders)
        male_names = ["Tendai", "Tafadzwa", "Blessing", "Tinashe", "Kudakwashe"]
        for i, name in enumerate(male_names):
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
                    city="Harare",
                    bio=f"Hi! I'm {name}, looking for fun social experiences in Harare.",
                    is_verified=True,
                    wallet_balance=Decimal(random.randint(50, 500)),
                    date_of_birth=datetime.now().date() - timedelta(days=random.randint(6570, 14600))
                )
                self.stdout.write(f"  ✅ Created male user: {user.username}")
        
        # Create female users (acceptors)
        female_names = ["Rutendo", "Tarisai", "Tendekai", "Rumbidzai", "Tendai"]
        for i, name in enumerate(female_names):
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
                    city="Harare",
                    bio=f"Hi! I'm {name}, excited to meet new people and have amazing experiences.",
                    is_verified=True,
                    wallet_balance=Decimal(random.randint(20, 200)),
                    date_of_birth=datetime.now().date() - timedelta(days=random.randint(6570, 14600))
                )
                self.stdout.write(f"  ✅ Created female user: {user.username}")

    def create_bids(self):
        """Create dummy bids"""
        self.stdout.write("💰 Creating dummy bids...")
        
        male_users = User.objects.filter(user_type="M")
        categories = EventCategory.objects.all()
        
        if not male_users.exists() or not categories.exists():
            self.stdout.write("  ❌ No male users or categories found.")
            return
        
        bid_data = [
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
            },
            {
                "title": "Want to try the new restaurant in Borrowdale",
                "description": "I've heard great things about this place. Let's try it together!",
                "bid_amount": Decimal("100.00"),
                "event_date": datetime.now() + timedelta(days=2, hours=19)
            },
            {
                "title": "Looking for someone to watch the new Marvel movie",
                "description": "The new movie looks fantastic! Let's watch it together.",
                "bid_amount": Decimal("80.00"),
                "event_date": datetime.now() + timedelta(days=4, hours=20)
            },
            {
                "title": "Need company for the football match",
                "description": "Exciting match this weekend! Let's cheer together.",
                "bid_amount": Decimal("120.00"),
                "event_date": datetime.now() + timedelta(days=5, hours=15)
            }
        ]
        
        for i, bid_info in enumerate(bid_data):
            user = male_users[i % len(male_users)]
            category = categories[i % len(categories)]
            
            if not Bid.objects.filter(title=bid_info["title"]).exists():
                bid = Bid.objects.create(
                    user=user,
                    title=bid_info["title"],
                    description=bid_info["description"],
                    event_category=category,
                    event_date=bid_info["event_date"],
                    event_location="Harare, Zimbabwe",
                    event_address="123 Main Street, Harare",
                    bid_amount=bid_info["bid_amount"],
                    commission_amount=bid_info["bid_amount"] * Decimal("0.15")
                )
                self.stdout.write(f"  ✅ Created bid: {bid.title}")
