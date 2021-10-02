from django.conf import settings

def pyplenary_settings(request):
    return {
    	'NAVBAR_NAME': settings.PYPLENARY_NAVBAR_NAME,
        'SITE_NAME': settings.PYPLENARY_SITE_NAME,
        'SITE_TAGLINE': settings.PYPLENARY_SITE_TAGLINE,
        'PYPLENARY_TZ': settings.PYPLENARY_TZ,
    }
