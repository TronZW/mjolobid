#!/usr/bin/env python
"""
Quick script to create a superuser with predefined credentials.
"""

import os
import sys
import django

# Add the project directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set Django settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mjolobid.settings_render')

# Setup Django
django.setup()

from django.contrib.auth import get_user_model

def create_quick_superuser():
    """Create a superuser with predefined credentials"""
    User = get_user_model()
    
    # Superuser credentials
    username = "tron"
    email = "tronmapzy@gmail.com"
    password = "admin123"  # Change this to something more secure
    
    try:
        # Check if superuser already exists
        if User.objects.filter(username=username).exists():
            print(f"✅ Superuser '{username}' already exists!")
            return
        
        # Create superuser
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        
        print("✅ Superuser created successfully!")
        print(f"Username: {username}")
        print(f"Email: {email}")
        print(f"Password: {password}")
        print("\n🔗 Admin Panel: https://mjolobid.onrender.com/admin/")
        print("⚠️  Remember to change the password after first login!")
        
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")

if __name__ == "__main__":
    create_quick_superuser()
