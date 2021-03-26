# -*- coding: utf-8 -*-

from pathlib import Path
import os

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/3.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'ubfxhi$qrj&9$s&^g5lmru3l03h5azq&w@mfso0+*beq71x!8t'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

# ALLOWED_HOSTS = ['*']

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

# DATABASES = {
#     'default': {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': BASE_DIR / 'db.sqlite3',
#     }
# }


REDIS_URL = os.environ['REDIS_URL'] if os.environ.get('REDIS_URL') else None

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

PYPLENARY_NAVBAR_NAME = 'AMSA Council 1 2021'
PYPLENARY_SITE_NAME = 'AMSA National Council 1 2021'
PYPLENARY_SITE_TAGLINE = '26-28 March 2021 🍊'
PYPLENARY_AGENDA_URI = 'https://drive.google.com/uc?id=1dP1j0mX7OVNnjB1p1XP1ZxJV0MxI9T33'
PYPLENARY_REPORTS_URI = 'https://drive.google.com/uc?id=1HciBoCsCMPA3sIEV83WRE3pnZGSGCE8V'
PYPLENARY_SOCIALS_URI = 'https://drive.google.com/uc?id=1Qvw7y6uaWquAQ8osxprv0GIsm3ZWPGaY'
PYPLENARY_NODES_URI = 'https://drive.google.com/uc?id=1pS2Gj8P1wKPC3IYxcEug7bVyAG8rkV0Q'
# PRODUCTION SETTINGS

# Configure the domain name using the environment variable
# that Azure automatically creates for us.
# ALLOWED_HOSTS = [os.environ['WEBSITE_HOSTNAME']] if 'WEBSITE_HOSTNAME' in os.environ else []
ALLOWED_HOSTS = ['*']

# whitenoise
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'  
# STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')


DATABASES = {}

if all(x in os.environ for x in ['DBHOST', 'DBNAME', 'DBUSER', 'DBPASS']):
    # DBHOST is only the server name, not the full URL
    hostname = os.environ['DBHOST']

    # Configure Postgres database; the full username is username@servername,
    # which we construct using the DBHOST value.
    DATABASES['default'] = {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ['DBNAME'],
        'HOST': hostname + ".postgres.database.azure.com",
        'USER': os.environ['DBUSER'] + "@" + hostname,
        'PASSWORD': os.environ['DBPASS'] 
    }

CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
        'LOCATION': 'django_cache',
    }
}

WEB_DOMAIN = "https://council.amsa.org.au"

#auto email stuff
EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_USE_SSL = True
EMAIL_PORT = 465
EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER', None)
EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD', None)

# TEMP PASSWORD FOR NEW USERS

if not os.environ.get('USER_TEMP_PASSWORD'):
    USER_TEMP_PASSWORD = 'tempPassword'

# OPEN REGO
REGO_OPEN = True if os.environ.get('REGO_OPEN', '0') == "1" else False

LOADERIO_TOKEN = '71c1d90d203bf7dd2d56ce4203cb238f' # For https://loader.io/

# LOAD DEVELOPMENT SETTINGS IF ENVIRON SET
if os.environ.get('DJANGO_DEVELOPMENT'):
    from .settingsDev import *
