#!/bin/bash

echo "🚀 Starting MjoloBid deployment..."

# Run migrations
echo "📊 Running database migrations..."
# Ensure DB directory exists if using sqlite on disk
if [ -n "${SQLITE_DB_PATH}" ]; then
  echo "🗄️  Ensuring SQLite directory exists for ${SQLITE_DB_PATH}..."
  DB_DIR=$(dirname "${SQLITE_DB_PATH}")
  mkdir -p "${DB_DIR}"
fi
python manage.py migrate --noinput

# Ensure media directory exists on mounted disk
if [ -n "${MEDIA_ROOT}" ]; then
  echo "🗂️  Ensuring MEDIA_ROOT exists at ${MEDIA_ROOT}..."
  mkdir -p "${MEDIA_ROOT}"
fi

# Create superuser (optional, gated)
if [ "${CREATE_SUPERUSER_ON_DEPLOY:-false}" = "true" ]; then
  echo "👤 Creating superuser..."
  python manage.py create_superuser
else
  echo "⏭️  Skipping superuser creation (CREATE_SUPERUSER_ON_DEPLOY=false)"
fi

# Seed data (optional, gated)
if [ "${SEED_ON_DEPLOY:-false}" = "true" ]; then
  echo "🌱 Seeding database with dummy data..."
  python manage.py seed_data
else
  echo "⏭️  Skipping data seeding (SEED_ON_DEPLOY=false)"
fi

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --noinput

# Start server
echo "🌐 Starting Gunicorn server..."
gunicorn mjolobid.wsgi:application --bind 0.0.0.0:$PORT
