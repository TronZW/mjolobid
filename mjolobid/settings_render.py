"""
Render-specific settings for mjolobid project.
"""
import os
from pathlib import Path
from decouple import config
import logging

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = ['*']

# Application definition - Only essential apps
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'accounts',
    'bids',
    'offers',
    'payments',
    'notifications',
    'messaging',
    'admin_dashboard',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'mjolobid.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'notifications.context_processors.webpush_settings',
            ],
        },
    },
]

WSGI_APPLICATION = 'mjolobid.wsgi.application'

# Database configuration - Use SQLite on Render disk
# This ensures persistence across deploys
SQLITE_DB_PATH = '/var/disk1/db.sqlite3'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': SQLITE_DB_PATH,
    }
}

# Log effective DB configuration at startup for diagnostics
try:
    _db = DATABASES.get('default', {})
    _engine = _db.get('ENGINE', '')
    _name = _db.get('NAME', '')
    logging.getLogger('startup').info(f"DB_ENGINE={_engine} DB_NAME={_name}")
except Exception:
    pass

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Africa/Harare'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
# STATICFILES_DIRS = [os.path.join(BASE_DIR, 'static')]  # Commented out - directory doesn't exist

# Media files - Use GitHub-backed storage when configured; otherwise local
USE_GITHUB_STORAGE = config('USE_GITHUB_STORAGE', default=True, cast=bool)
GITHUB_TOKEN = config('GITHUB_TOKEN', default='')
GITHUB_REPO = config('GITHUB_REPO', default='')

if USE_GITHUB_STORAGE and GITHUB_TOKEN and GITHUB_REPO:
    DEFAULT_FILE_STORAGE = 'accounts.storage.GitHubStorage'
    MEDIA_URL = '/'
    MEDIA_ROOT = ''
else:
    MEDIA_URL = '/media/'
    MEDIA_ROOT = os.environ.get('MEDIA_ROOT', os.path.join(BASE_DIR, 'media'))

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom user model
AUTH_USER_MODEL = 'accounts.User'

# Django REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
}

# CORS settings
CORS_ALLOWED_ORIGINS = [
    "https://your-app-name.onrender.com",
]

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

# HTTPS settings
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Email configuration
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = config('EMAIL_HOST', default='smtp.gmail.com')
EMAIL_PORT = config('EMAIL_PORT', default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config('EMAIL_HOST_USER', default='')
EMAIL_HOST_PASSWORD = config('EMAIL_HOST_PASSWORD', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='MjoloBid <mjolobidapp@gmail.com>')
SERVER_EMAIL = config('SERVER_EMAIL', default='MjoloBid <mjolobidapp@gmail.com>')
SITE_URL = config('SITE_URL', default='https://your-app-name.onrender.com')

# Stripe configuration
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')
STRIPE_WEBHOOK_SECRET = config('STRIPE_WEBHOOK_SECRET', default='')

# App specific settings
MJOLOBID_SETTINGS = {
    'COMMISSION_RATE': 0.15,  # 15% commission
    'WOMEN_SUBSCRIPTION_FEE': 3.00,  # $3 subscription fee
    'MIN_BID_AMOUNT': 5.00,  # Minimum bid amount
    'MAX_BID_AMOUNT': 500.00,  # Maximum bid amount
}

# Web push (VAPID) settings
WEBPUSH_VAPID_PUBLIC_KEY = config('WEBPUSH_VAPID_PUBLIC_KEY', default='')
WEBPUSH_VAPID_PRIVATE_KEY = config('WEBPUSH_VAPID_PRIVATE_KEY', default='')
WEBPUSH_VAPID_CONTACT_EMAIL = config('WEBPUSH_VAPID_CONTACT_EMAIL', default='support@mjolobid.com')

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}
