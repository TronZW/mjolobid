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
        
        # Create male users (bidders) with proper Zimbabwean names
        male_users_data = [
            {"first_name": "Tendai", "last_name": "Moyo", "username": "tendai_moyo"},
            {"first_name": "Tafadzwa", "last_name": "Ncube", "username": "tafadzwa_ncube"},
            {"first_name": "Blessing", "last_name": "Sibanda", "username": "blessing_sibanda"},
            {"first_name": "Tinashe", "last_name": "Mpofu", "username": "tinashe_mpofu"},
            {"first_name": "Kudakwashe", "last_name": "Ndlovu", "username": "kudakwashe_ndlovu"},
            {"first_name": "Tatenda", "last_name": "Mukamuri", "username": "tatenda_mukamuri"},
            {"first_name": "Tawanda", "last_name": "Chigwada", "username": "tawanda_chigwada"},
            {"first_name": "Farai", "last_name": "Mazvita", "username": "farai_mazvita"}
        ]
        
        for user_data in male_users_data:
            if not User.objects.filter(username=user_data["username"]).exists():
                user = User.objects.create_user(
                    username=user_data["username"],
                    email=f"{user_data['username']}@gmail.com",
                    password="password123",
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    gender="M",
                    user_type="M",
                    phone_number=f"077{random.randint(1000000, 9999999)}",
                    city=random.choice(["Harare", "Bulawayo", "Gweru", "Mutare"]),
                    bio=f"Hi! I'm {user_data['first_name']} {user_data['last_name']}, looking for fun social experiences. Let's create amazing memories together!",
                    is_verified=random.choice([True, False]),
                    wallet_balance=Decimal(random.randint(50, 500)),
                    date_of_birth=datetime.now().date() - timedelta(days=random.randint(6570, 14600))
                )
                self.stdout.write(f"  ✅ Created male user: {user.first_name} {user.last_name} ({user.username})")
        
        # Create female users (acceptors) with proper Zimbabwean names
        female_users_data = [
            {"first_name": "Rutendo", "last_name": "Moyo", "username": "rutendo_moyo"},
            {"first_name": "Tarisai", "last_name": "Ncube", "username": "tarisai_ncube"},
            {"first_name": "Tendekai", "last_name": "Sibanda", "username": "tendekai_sibanda"},
            {"first_name": "Rumbidzai", "last_name": "Mpofu", "username": "rumbidzai_mpofu"},
            {"first_name": "Tendai", "last_name": "Ndlovu", "username": "tendai_ndlovu"},
            {"first_name": "Rutendo", "last_name": "Mukamuri", "username": "rutendo_mukamuri"},
            {"first_name": "Tarisai", "last_name": "Chigwada", "username": "tarisai_chigwada"},
            {"first_name": "Tendekai", "last_name": "Mazvita", "username": "tendekai_mazvita"}
        ]
        
        for user_data in female_users_data:
            if not User.objects.filter(username=user_data["username"]).exists():
                user = User.objects.create_user(
                    username=user_data["username"],
                    email=f"{user_data['username']}@gmail.com",
                    password="password123",
                    first_name=user_data["first_name"],
                    last_name=user_data["last_name"],
                    gender="F",
                    user_type="F",
                    phone_number=f"077{random.randint(1000000, 9999999)}",
                    city=random.choice(["Harare", "Bulawayo", "Gweru", "Mutare"]),
                    bio=f"Hi! I'm {user_data['first_name']} {user_data['last_name']}, excited to meet new people and have amazing experiences. Let's make memories together!",
                    is_verified=random.choice([True, False]),
                    wallet_balance=Decimal(random.randint(20, 200)),
                    date_of_birth=datetime.now().date() - timedelta(days=random.randint(6570, 14600))
                )
                self.stdout.write(f"  ✅ Created female user: {user.first_name} {user.last_name} ({user.username})")

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
                "description": "Great night out planned at Club 7! Let's dance, have drinks, and make amazing memories together. Perfect for someone who loves to have fun!",
                "bid_amount": Decimal("150.00"),
                "event_date": datetime.now() + timedelta(days=1, hours=20)
            },
            {
                "title": "Need a date for the Harare Jazz Festival",
                "description": "The annual Jazz Festival is this weekend and I'd love to share this amazing musical experience with someone special. Great music, great vibes!",
                "bid_amount": Decimal("200.00"),
                "event_date": datetime.now() + timedelta(days=3, hours=19)
            },
            {
                "title": "Want to try the new restaurant in Borrowdale",
                "description": "I've heard amazing things about this new restaurant in Borrowdale. Let's try their signature dishes together and enjoy great conversation over dinner!",
                "bid_amount": Decimal("100.00"),
                "event_date": datetime.now() + timedelta(days=2, hours=19)
            },
            {
                "title": "Looking for someone to watch the new Marvel movie",
                "description": "The new Marvel movie looks absolutely fantastic! I'd love to watch it with someone who appreciates great cinema. Popcorn and fun guaranteed!",
                "bid_amount": Decimal("80.00"),
                "event_date": datetime.now() + timedelta(days=4, hours=20)
            },
            {
                "title": "Need company for the Dynamos vs Highlanders match",
                "description": "Big football match this weekend! Dynamos vs Highlanders - it's going to be intense and exciting. Let's cheer together and enjoy the atmosphere!",
                "bid_amount": Decimal("120.00"),
                "event_date": datetime.now() + timedelta(days=5, hours=15)
            },
            {
                "title": "Looking for a beach day companion at Lake Chivero",
                "description": "Perfect weather for a beach day at Lake Chivero! Let's enjoy the sun, water activities, and maybe a picnic. Great way to relax and have fun!",
                "bid_amount": Decimal("180.00"),
                "event_date": datetime.now() + timedelta(days=6, hours=10)
            },
            {
                "title": "Want to attend the art exhibition at National Gallery",
                "description": "There's a beautiful art exhibition at the National Gallery featuring local Zimbabwean artists. Perfect for someone who appreciates culture and creativity!",
                "bid_amount": Decimal("90.00"),
                "event_date": datetime.now() + timedelta(days=7, hours=14)
            },
            {
                "title": "Need someone to go shopping with at Sam Levy's",
                "description": "Planning a shopping trip to Sam Levy's Village. Would love company to browse, try things on, and maybe grab coffee. Fun and relaxed day out!",
                "bid_amount": Decimal("110.00"),
                "event_date": datetime.now() + timedelta(days=8, hours=11)
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
