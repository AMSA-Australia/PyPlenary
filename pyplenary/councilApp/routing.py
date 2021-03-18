from django.urls import re_path

from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/speaker-list/$', consumers.SpeakerListConsumer.as_asgi()),
]
