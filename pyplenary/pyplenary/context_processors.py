from django.conf import settings

def pyplenary_settings(request):
    return {
        'SITE_NAME': settings.PYPLENARY_SITE_NAME,
        'SITE_TAGLINE': settings.PYPLENARY_SITE_TAGLINE
    }
