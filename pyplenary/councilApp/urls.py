from django.conf.urls import url, include
from django.contrib.auth import views as auth_views
from django.conf import settings
from django.conf.urls.static import static
from django.urls import path, reverse
from django.shortcuts import redirect
from django.views.generic import TemplateView
from . import views

#settings.STATIC_URL = '/static/'

urlpatterns = [
	path('', views.index),
	path('index.html', views.index),
	path('speaker_list/', views.speakerList),
	path('delegates/', views.delegates),
	path('profile/', views.profile),
	path('vote/', views.vote),
	path('login/', views.loginCustom),
	path('logout/', views.logoutCustom),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)