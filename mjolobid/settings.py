"""
Django settings for mjolobid project.
"""

from pathlib import Path
from decouple import config
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = config('SECRET_KEY', default='django-insecure-change-this-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = config('DEBUG', default=True, cast=bool)

ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0']

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'rest_framework',
    'corsheaders',
    'channels',
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
ASGI_APPLICATION = 'mjolobid.asgi.application'

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

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
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
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
    "http://localhost:3000",
    "http://127.0.0.1:3000",
]

# Channels configuration
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}

# Redis configuration
REDIS_URL = config('REDIS_URL', default='redis://127.0.0.1:6379/1')

# Celery configuration
CELERY_BROKER_URL = REDIS_URL
CELERY_RESULT_BACKEND = REDIS_URL

# Payment settings
STRIPE_PUBLISHABLE_KEY = config('STRIPE_PUBLISHABLE_KEY', default='')
STRIPE_SECRET_KEY = config('STRIPE_SECRET_KEY', default='')

# App specific settings
MJOLOBID_SETTINGS = {
    'COMMISSION_RATE': 0.15,  # 15% commission
    'WOMEN_SUBSCRIPTION_FEE': 3.00,  # $3 subscription fee
    'MIN_BID_AMOUNT': 5.00,  # Minimum bid amount
    'MAX_BID_AMOUNT': 500.00,  # Maximum bid amount
}

# Email configuration - SendGrid SMTP (recommended)
# NOTE: Put your actual API key in the SENDGRID_API_KEY environment variable (both locally and on Render).
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.sendgrid.net'
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = 'apikey'  # This literal string is required by SendGrid
EMAIL_HOST_PASSWORD = config('SENDGRID_API_KEY', default='')
DEFAULT_FROM_EMAIL = config('DEFAULT_FROM_EMAIL', default='MjoloBid <mjolobidapp@gmail.com>')

SERVER_EMAIL = DEFAULT_FROM_EMAIL
SITE_URL = config('SITE_URL', default='http://localhost:8000')

# Payment Gateway Settings
# EcoCash Configuration
ECOCASH_CLIENT_ID = config('ECOCASH_CLIENT_ID', default='')
ECOCASH_CLIENT_SECRET = config('ECOCASH_CLIENT_SECRET', default='')
ECOCASH_MERCHANT_ID = config('ECOCASH_MERCHANT_ID', default='')
ECOCASH_API_URL = config('ECOCASH_API_URL', default='https://api.ecocash.co.zw')
ECOCASH_SANDBOX = config('ECOCASH_SANDBOX', default=False, cast=bool)

# Paynow Configuration
PAYNOW_INTEGRATION_ID = config('PAYNOW_INTEGRATION_ID', default='')
PAYNOW_INTEGRATION_KEY = config('PAYNOW_INTEGRATION_KEY', default='')
PAYNOW_API_URL = config('PAYNOW_API_URL', default='https://www.paynow.co.zw/Interface/API')
PAYNOW_SANDBOX = config('PAYNOW_SANDBOX', default=False, cast=bool)

# Pesepay Configuration
PESEPAY_API_KEY = config('PESEPAY_API_KEY', default='')
PESEPAY_SECRET_KEY = config('PESEPAY_SECRET_KEY', default='')
PESEPAY_API_URL = config('PESEPAY_API_URL', default='https://api.pesepay.com')
PESEPAY_SANDBOX = config('PESEPAY_SANDBOX', default=False, cast=bool)

# Default payment gateway
DEFAULT_PAYMENT_GATEWAY = config('DEFAULT_PAYMENT_GATEWAY', default='ECOCASH')

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
