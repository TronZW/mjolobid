#!/usr/bin/env python
"""
Script to create a superuser for the deployed MjoloBid application.
Run this script to create an admin user.
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
from django.core.management import execute_from_command_line

def create_superuser():
    """Create a superuser interactively"""
    print("Creating superuser for MjoloBid...")
    print("=" * 50)
    
    try:
        # Run the createsuperuser command
        execute_from_command_line(['manage.py', 'createsuperuser'])
        print("\n✅ Superuser created successfully!")
        print("You can now login to the admin panel at: https://mjolobid.onrender.com/admin/")
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")

if __name__ == "__main__":
    create_superuser()
