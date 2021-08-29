from .settings import *
import os

# DEVELOPMENT DATABASE
DEV_CONFIG_FILE_URL = 'https://drive.google.com/uc?id=1FJFrtS2sJ9kk9a1Bsokt0cBYg05-ESpn'
CUSTOM_CONFIGS = readConfigYAMLFromHTML(DEV_CONFIG_FILE_URL)

DEBUG = True

ALLOWED_HOSTS = ["*"]

SECURE_SSL_REDIRECT = False

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

WEB_DOMAIN = "http://127.0.0.1:8000"
