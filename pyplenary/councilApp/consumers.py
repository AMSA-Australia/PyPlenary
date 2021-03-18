import json

from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer

class SpeakerListConsumer(WebsocketConsumer):
    def connect(self):
        async_to_sync(self.channel_layer.group_add)('speakerlist', self.channel_name)
        self.accept()

    def disconnect(self, code):
        pass

    def receive(self, text_data):
        pass

    def speakerlist_updated(self, data):
        self.send(text_data=json.dumps(data))
