#!/usr/bin/env python
"""
Development server runner for MjoloBid
This script sets up the development environment and runs the Django server
"""

import os
import sys
import subprocess
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed:")
        print(f"Error: {e.stderr}")
        return False

def check_requirements():
    """Check if required software is installed"""
    print("🔍 Checking requirements...")
    
    # Check Python version
    if sys.version_info < (3, 8):
        print("❌ Python 3.8+ is required")
        return False
    
    # Check if Redis is running
    try:
        import redis
        r = redis.Redis(host='localhost', port=6379, db=1)
        r.ping()
        print("✅ Redis is running")
    except:
        print("⚠️  Redis is not running. Please start Redis server:")
        print("   redis-server")
        return False
    
    return True

def setup_environment():
    """Set up the development environment"""
    print("🚀 Setting up MjoloBid development environment...")
    
    # Check if .env file exists
    if not Path('.env').exists():
        print("⚠️  .env file not found. Creating from example...")
        if Path('env.example').exists():
            import shutil
            shutil.copy('env.example', '.env')
            print("✅ Created .env file from example")
        else:
            print("❌ env.example file not found")
            return False
    
    return True

def run_migrations():
    """Run Django migrations"""
    return run_command("python manage.py makemigrations", "Creating migrations")

def apply_migrations():
    """Apply Django migrations"""
    return run_command("python manage.py migrate", "Applying migrations")

def create_superuser():
    """Create Django superuser if it doesn't exist"""
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    if not User.objects.filter(is_superuser=True).exists():
        print("\n👤 Creating superuser...")
        print("Please enter the following details:")
        
        username = input("Username: ") or "admin"
        email = input("Email: ") or "admin@mjolobid.com"
        password = input("Password: ") or "admin123"
        
        try:
            User.objects.create_superuser(username=username, email=email, password=password)
            print("✅ Superuser created successfully")
        except Exception as e:
            print(f"❌ Failed to create superuser: {e}")
            return False
    
    return True

def load_sample_data():
    """Load sample data for development"""
    print("\n📊 Loading sample data...")
    
    # Create event categories
    from bids.models import EventCategory
    
    categories = [
        {'name': 'Club Night', 'icon': '🎉', 'description': 'Nightclub events and parties'},
        {'name': 'Dinner', 'icon': '🍽️', 'description': 'Restaurant dinners and fine dining'},
        {'name': 'Concert', 'icon': '🎵', 'description': 'Live music and concerts'},
        {'name': 'Festival', 'icon': '🎪', 'description': 'Music festivals and outdoor events'},
        {'name': 'Sports', 'icon': '⚽', 'description': 'Sports events and games'},
        {'name': 'Party', 'icon': '🎊', 'description': 'House parties and social gatherings'},
    ]
    
    for cat_data in categories:
        category, created = EventCategory.objects.get_or_create(
            name=cat_data['name'],
            defaults=cat_data
        )
        if created:
            print(f"✅ Created category: {category.name}")
    
    return True

def start_server():
    """Start the Django development server"""
    print("\n🌐 Starting Django development server...")
    print("Server will be available at: http://127.0.0.1:8000")
    print("Admin panel: http://127.0.0.1:8000/admin")
    print("\nPress Ctrl+C to stop the server")
    
    try:
        subprocess.run("python manage.py runserver", shell=True)
    except KeyboardInterrupt:
        print("\n👋 Server stopped")

def main():
    """Main function"""
    print("🎯 MjoloBid Development Server")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        print("\n❌ Requirements check failed. Please fix the issues above.")
        return
    
    # Setup environment
    if not setup_environment():
        print("\n❌ Environment setup failed.")
        return
    
    # Run migrations
    if not run_migrations():
        print("\n❌ Migration creation failed.")
        return
    
    if not apply_migrations():
        print("\n❌ Migration application failed.")
        return
    
    # Create superuser
    if not create_superuser():
        print("\n❌ Superuser creation failed.")
        return
    
    # Load sample data
    if not load_sample_data():
        print("\n❌ Sample data loading failed.")
        return
    
    print("\n✅ Setup completed successfully!")
    
    # Start server
    start_server()

if __name__ == "__main__":
    main()
