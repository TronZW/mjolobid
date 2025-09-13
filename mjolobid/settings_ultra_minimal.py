"""
Ultra-minimal Django settings for Railway health check.
"""
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-ultra-minimal')

DEBUG = False

ALLOWED_HOSTS = ['*']

# Minimal apps
INSTALLED_APPS = [
    'django.contrib.contenttypes',
]

# Minimal middleware
MIDDLEWARE = [
    'django.middleware.common.CommonMiddleware',
]

ROOT_URLCONF = 'mjolobid.urls_minimal'

# No templates needed
TEMPLATES = []

WSGI_APPLICATION = 'mjolobid.wsgi.application'

# Use in-memory database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

# No static files
STATIC_URL = None

# Minimal logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': True,
}
