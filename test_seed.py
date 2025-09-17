#!/usr/bin/env python
"""
Test script to verify data seeding works locally
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mjolobid.settings')

# Setup Django
django.setup()

from django.core.management import execute_from_command_line

def test_seeding():
    """Test the data seeding command"""
    print("🧪 Testing data seeding locally...")
    
    try:
        # Run the seed_data management command
        execute_from_command_line(['manage.py', 'seed_data'])
        print("✅ Local seeding test completed successfully!")
        
        # Check what was created
        from django.contrib.auth import get_user_model
        from bids.models import EventCategory, Bid
        
        User = get_user_model()
        
        print(f"📊 Results:")
        print(f"  👥 Users: {User.objects.count()}")
        print(f"  📂 Categories: {EventCategory.objects.count()}")
        print(f"  💰 Bids: {Bid.objects.count()}")
        
    except Exception as e:
        print(f"❌ Local seeding test failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_seeding()
