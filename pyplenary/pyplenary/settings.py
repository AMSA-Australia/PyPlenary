# -*- coding: utf-8 -*-
from pathlib import Path
import os
from .utils import *

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'tempKey')

# location of custom configurations file
# LOAD DEVELOPMENT SETTINGS IF ENVIRON SET
if os.environ.get('DJANGO_DEVELOPMENT'):
    # development environment
    CUSTOM_CONFIG_URL = 'https://drive.google.com/uc?id=1FJFrtS2sJ9kk9a1Bsokt0cBYg05-ESpn'
else:
    # production environment
    CUSTOM_CONFIG_URL = 'https://drive.google.com/uc?id=1851_s4XH7rQUrGQuU5zkZ1-ryBDPTqru'
CUSTOM_CONFIGS = readConfigYAMLFromHTML(CUSTOM_CONFIG_URL)

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG =  bool(int(CUSTOM_CONFIGS['DEBUG_MODE']))

ALLOWED_HOSTS = ['*']

# SECURE_SSL_REDIRECT = True

# Application definition

INSTALLED_APPS = [
    'channels',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'councilApp',    
    'crispy_forms',
    'django_extensions',
    'crispy_forms_semantic_ui',
] + ['whitenoise.runserver_nostatic']

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
] + ['whitenoise.middleware.WhiteNoiseMiddleware']

ROOT_URLCONF = 'pyplenary.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'scripts'),],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'pyplenary.context_processors.pyplenary_settings'
            ],
        },
    },
]

WSGI_APPLICATION = 'pyplenary.wsgi.application'
ASGI_APPLICATION = "pyplenary.asgi.application"

# Database
# https://docs.djangoproject.com/en/3.1/ref/settings/#databases

REDIS_URL = CUSTOM_CONFIGS['REDIS_URL']

CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [REDIS_URL],
        },
    },
}

# Login
LOGIN_URL = '/login/'
LOGIN_REDIRECT_URL = '/'

# Password validation
# https://docs.djangoproject.com/en/3.1/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/3.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'Australia/Melbourne'

USE_I18N = True

USE_L10N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/3.1/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'static')
STATICFILES_DIRS = []

CSRF_USE_SESSIONS = True

#CRISPY_TEMPLATE_PACK = 'semantic-ui'
CRISPY_TEMPLATE_PACK = 'bootstrap4'


# PYPLENARY SETTINGS
PYPLENARY_NAVBAR_NAME = CUSTOM_CONFIGS['PYPLENARY_NAVBAR_NAME']
PYPLENARY_SITE_NAME = CUSTOM_CONFIGS['PYPLENARY_SITE_NAME']
PYPLENARY_SITE_TAGLINE = CUSTOM_CONFIGS['PYPLENARY_SITE_TAGLINE']
PYPLENARY_AGENDA_URI = CUSTOM_CONFIGS['PYPLENARY_AGENDA_URI']
PYPLENARY_REPORTS_URI = CUSTOM_CONFIGS['PYPLENARY_REPORTS_URI']
PYPLENARY_POLICIES_URI = CUSTOM_CONFIGS['PYPLENARY_POLICIES_URI']
PYPLENARY_SOCIALS_URI = CUSTOM_CONFIGS['PYPLENARY_SOCIALS_URI']
PYPLENARY_NODES_URI = CUSTOM_CONFIGS['PYPLENARY_NODES_URI']
PYPLENARY_FACEBOOK_GROUP = CUSTOM_CONFIGS['PYPLENARY_FACEBOOK_GROUP']
PYPLENARY_TZ = CUSTOM_CONFIGS['PYPLENARY_TZ']


# PRODUCTION SETTINGS

# whitenoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'  
# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

DATABASES = {}

# DBHOST is only the server name, not the full URL

hostname = CUSTOM_CONFIGS['DBHOST']

# Configure Postgres database; the full username is username@servername,
# which we construct using the DBHOST value.
if os.environ.get('DJANGO_DEVELOPMENT'):
    # development environment
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
else:
    # production environment
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': CUSTOM_CONFIGS['DBNAME'],
        'HOST': hostname + CUSTOM_CONFIGS['DBDOMAIN'],
        'USER': CUSTOM_CONFIGS['DBUSER'] + "@" + hostname,
        'PASSWORD': os.environ.get('DBPASS')
    }

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache',
    }
}

WEB_DOMAIN = CUSTOM_CONFIGS['COUNCIL_URL']

#auto email stuff
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_SSL = True
EMAIL_PORT = 465
EMAIL_HOST_USER = CUSTOM_CONFIGS['EMAIL_HOST_USER']
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')

# TEMP PASSWORD FOR NEW USERS
USER_TEMP_PASSWORD = CUSTOM_CONFIGS['USER_TEMP_PASSWORD']

LOADERIO_TOKEN = '71c1d90d203bf7dd2d56ce4203cb238f' # For https://loader.io/

REGO_OPEN = True if CUSTOM_CONFIGS['REGO_OPEN'] in ("1", 1) else False
