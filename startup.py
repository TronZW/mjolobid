#!/usr/bin/env python
"""
Startup script to create superuser and start the application.
"""

import os
import sys
import django
import subprocess

def setup_django():
    """Setup Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'mjolobid.settings_render')
    django.setup()

def create_superuser():
    """Create superuser if it doesn't exist"""
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    username = "tron"
    email = "tronmapzy@gmail.com"
    password = "admin123"
    
    try:
        if not User.objects.filter(username=username).exists():
            user = User.objects.create_superuser(
                username=username,
                email=email,
                password=password
            )
            print(f"✅ Superuser '{username}' created successfully!")
        else:
            print(f"✅ Superuser '{username}' already exists!")
    except Exception as e:
        print(f"❌ Error creating superuser: {e}")

def run_migrations():
    """Run database migrations"""
    try:
        subprocess.run(['python', 'manage.py', 'migrate', '--noinput'], check=True)
        print("✅ Migrations completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Migration failed: {e}")

def collect_static():
    """Collect static files"""
    try:
        subprocess.run(['python', 'manage.py', 'collectstatic', '--noinput'], check=True)
        print("✅ Static files collected successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Static collection failed: {e}")

def seed_data():
    """Seed the database with dummy data"""
    try:
        subprocess.run(['python', 'seed_data.py'], check=True)
        print("✅ Data seeding completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Data seeding failed: {e}")

def start_gunicorn():
    """Start Gunicorn server"""
    port = os.environ.get('PORT', '8000')
    try:
        subprocess.run([
            'gunicorn', 
            'mjolobid.wsgi:application', 
            '--bind', f'0.0.0.0:{port}'
        ], check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Gunicorn failed: {e}")

if __name__ == "__main__":
    print("🚀 Starting MjoloBid application...")
    
    # Setup Django
    setup_django()
    
    # Run migrations
    run_migrations()
    
    # Collect static files
    collect_static()
    
    # Create superuser
    create_superuser()
    
    # Seed data
    print("🌱 Seeding database with dummy data...")
    seed_data()
    
    # Start server
    print("🌐 Starting Gunicorn server...")
    start_gunicorn()
