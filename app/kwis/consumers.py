from channels.generic.websocket import WebsocketConsumer
from asgiref.sync import async_to_sync
import json


class RefreshConsumer(WebsocketConsumer):
    def connect(self):
        self.group_name = "refresh_group"
        async_to_sync(self.channel_layer.group_add)(
            self.group_name, self.channel_name
        )
        self.accept()

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.group_name, self.channel_name
        )

    def refresh_page(self, event):
        self.send(text_data=json.dumps({"action": "refresh"}))
