#!/bin/bash

echo "🚀 Starting MjoloBid deployment..."

# Run migrations
echo "📊 Running database migrations..."
python manage.py migrate --noinput

# Create superuser
echo "👤 Creating superuser..."
python manage.py create_superuser

# Seed data
echo "🌱 Seeding database with dummy data..."
python manage.py seed_data

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Start server
echo "🌐 Starting Gunicorn server..."
gunicorn mjolobid.wsgi:application --bind 0.0.0.0:$PORT
