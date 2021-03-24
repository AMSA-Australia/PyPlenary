import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

from django.core.cache import caches

from .models import *

class SpeakerListConsumer(WebsocketConsumer):
    def connect(self):
        async_to_sync(self.channel_layer.group_add)('speakerlist', self.channel_name)
        self.accept()
        
        delegate = self.scope['user'].delegate
        speakers = [s.to_json() for s in Speaker.objects.all()]
        self.send(text_data=json.dumps({'type': 'init', 'delegate_id': delegate.id, 'mode': caches['default'].get('speaker_mode', 'standard'), 'speakerlist': speakers}))

    def disconnect(self, code):
        pass

    def receive(self, text_data):
        pass

    def speakerlist_updated(self, data):
        self.send(text_data=json.dumps(data))
