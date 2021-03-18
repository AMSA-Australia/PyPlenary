from .settings import *
import os

# DEVELOPMENT DATABASE

DEBUG = True

ALLOWED_HOSTS = ["*"]

SECURE_SSL_REDIRECT = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}