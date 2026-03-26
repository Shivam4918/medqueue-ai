#medqueue/settings.py

"""
Django settings for medqueue project.
"""

import os
from pathlib import Path
import dj_database_url   # ✅ ADDED

from dotenv import load_dotenv
load_dotenv()

import pymysql
pymysql.install_as_MySQLdb()

BASE_DIR = Path(__file__).resolve().parent.parent


SECRET_KEY = os.getenv('SECRET_KEY', 'fallback-secret-for-dev')

DEBUG = os.getenv('DEBUG', 'True').lower() in ('1', 'true', 'yes')

# ✅ UPDATED (safe for local + railway)
ALLOWED_HOSTS = os.getenv(
    'ALLOWED_HOSTS',
    'localhost,127.0.0.1,.railway.app'
).split(',')


INSTALLED_APPS = [
    "daphne",
    'channels',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.humanize',

    'rest_framework',
    'widget_tweaks',

    'users',
    'hospitals',
    'doctors',
    'patients',
    'token_queue',
    'api',
    'dashboard',
    "notifications",
    "analytics",
]


MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',

    # ✅ ADDED (static files production safe)
    'whitenoise.middleware.WhiteNoiseMiddleware',

    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]


ROOT_URLCONF = 'medqueue.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [ BASE_DIR / "templates" ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'medqueue.wsgi.application'
ASGI_APPLICATION = 'medqueue.asgi.application'

REDIS_URL = os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/0')


# ==============================
# DATABASE CONFIG (SAFE HYBRID)
# ==============================

if os.getenv("DATABASE_URL"):
    # 🚀 Railway PostgreSQL
    DATABASES = {
        'default': dj_database_url.config(conn_max_age=600)
    }
else:
    # 💻 Local MySQL (your existing)
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.mysql',
            'NAME': os.getenv('MYSQL_DB', 'medqueue'),
            'USER': os.getenv('MYSQL_USER', 'medqueue_user'),
            'PASSWORD': os.getenv('MYSQL_PASS', 'Shivam4918@'),
            'HOST': os.getenv('MYSQL_HOST', '127.0.0.1'),
            'PORT': os.getenv('MYSQL_PORT', '3307'),
            'OPTIONS': {
                'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
            },
        }
    }


# MongoDB
MONGO_URL = os.getenv('MONGO_URL', 'mongodb://127.0.0.1:27017')


AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]


LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'Asia/Kolkata'

USE_I18N = True
USE_TZ = True

PASSWORD_RESET_TIMEOUT = 900


# ==============================
# STATIC FILES
# ==============================

STATIC_URL = 'static/'

STATICFILES_DIRS = [
    BASE_DIR / "static"
]

# ✅ ADDED
STATIC_ROOT = BASE_DIR / "staticfiles"

# ✅ ADDED (production safe)
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"


DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
AUTH_USER_MODEL = "users.User"


LOGIN_URL = "/auth/patient/login/"
LOGIN_REDIRECT_URL = "/dashboard/superadmin/dashboard/"
LOGOUT_REDIRECT_URL = "/"


# ==============================
# MEDIA FILES
# ==============================

MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"


# ==============================
# CHANNELS (UPDATED SAFE)
# ==============================

CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")],
        },
    },
}


# ==============================
# CELERY
# ==============================

CELERY_BROKER_URL = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")
CELERY_ACCEPT_CONTENT = ["json"]
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_BACKEND = os.getenv("REDIS_URL", "redis://127.0.0.1:6379/0")


# ==============================
# EMAIL
# ==============================

EMAIL_BACKEND = os.getenv("EMAIL_BACKEND")
EMAIL_HOST = os.getenv("EMAIL_HOST")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USE_TLS = os.getenv("EMAIL_USE_TLS") == "True"
EMAIL_HOST_USER = os.getenv("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = os.getenv("DEFAULT_FROM_EMAIL")