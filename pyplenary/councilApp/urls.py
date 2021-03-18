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
	path('speaker_list/add', views.speakerAdd),
	path('speaker_list/inner', views.speakerListInner),
	path('delegates/', views.delegates),
	path('proxy/', views.proxy),
	path('ajax/nominateProxy/', views.proxyNominate),
	path('ajax/retractProxy/', views.proxyRetract),
	path('ajax/resignProxy/', views.proxyResign),
	path('poll/', views.poll),
	path('poll/create/', views.createPoll),
	path('poll/close/<int:pollId>/', views.closePoll),
	path('poll/<int:pollId>/', views.pollInfo),
	path('vote/<int:pollId>/', views.voteOnPoll),
	path('ajax/getActiveVotes/', views.ajaxGetCastVotes),
	path('ajax/submitVotes/', views.ajaxSubmitVotes),
	path('agenda/', views.agenda),
	path('login/', views.loginCustom),
	path('logout/', views.logoutCustom),
	path('password_change_request/', views.passwordResetLinkRequest),
	path('password_reset/<str:token>', views.passwordReset),
	path('profile/', views.profile),
] + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
