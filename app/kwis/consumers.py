from channels.generic.websocket import AsyncWebsocketConsumer
import json


class RankingConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.group_name = "ranking_updates"
        await self.channel_layer.group_add(self.group_name, self.channel_name)
        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(self.group_name, self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        # if quizmaster triggers "reveal_next"
        if data.get("action") == "reveal_next":
            await self.channel_layer.group_send(
                self.group_name,
                {
                    "type": "reveal_next",
                }
            )

    async def reveal_next(self, event):
        # broadcast to all connected clients
        await self.send(text_data=json.dumps({
            "action": "reveal_next"
        }))
