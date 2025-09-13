#!/usr/bin/env python
"""
Deployment script for MjoloBid
"""
import os
import sys
import django
from django.core.management import execute_from_command_line

def setup_production():
    """Setup production environment"""
    print("🚀 Setting up production environment...")
    
    # Set production settings
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mjolobid.settings_production')
    
    # Setup Django
    django.setup()
    
    # Run migrations
    print("📦 Running database migrations...")
    execute_from_command_line(['manage.py', 'migrate'])
    
    # Collect static files
    print("📁 Collecting static files...")
    execute_from_command_line(['manage.py', 'collectstatic', '--noinput'])
    
    # Create superuser if it doesn't exist
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if not User.objects.filter(is_superuser=True).exists():
        print("👤 Creating superuser...")
        execute_from_command_line(['manage.py', 'createsuperuser', '--noinput'])
    
    print("✅ Production setup complete!")

if __name__ == '__main__':
    setup_production()
