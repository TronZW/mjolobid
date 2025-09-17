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
    try:
        from django.contrib.auth import get_user_model
        
        User = get_user_model()
        username = "tron"
        email = "tronmapzy@gmail.com"
        password = "admin123"
        
        # Check if the User table exists by trying to query it
        try:
            User.objects.count()
        except Exception as table_error:
            print(f"❌ User table doesn't exist yet: {table_error}")
            print("⚠️  Skipping superuser creation - migrations may not have completed")
            return
        
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
        print("⚠️  Continuing without superuser creation...")

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
        # Check if database tables exist first
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Test if we can query the database
        try:
            User.objects.count()
        except Exception as db_error:
            print(f"❌ Database not ready for seeding: {db_error}")
            print("⚠️  Skipping data seeding - database may not be properly migrated")
            return
        
        # Try the comprehensive seeding first
        subprocess.run(['python', 'seed_data.py'], check=True)
        print("✅ Data seeding completed successfully!")
    except subprocess.CalledProcessError as e:
        print(f"❌ Comprehensive seeding failed: {e}")
        print("🔄 Trying quick seeding as fallback...")
        try:
            # Fallback to quick seeding
            subprocess.run(['python', 'quick_seed.py'], check=True)
            print("✅ Quick data seeding completed successfully!")
        except subprocess.CalledProcessError as e2:
            print(f"❌ Quick seeding also failed: {e2}")
            print("⚠️  Continuing without data seeding...")
    except Exception as e:
        print(f"❌ Error during data seeding setup: {e}")
        print("⚠️  Continuing without data seeding...")

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
