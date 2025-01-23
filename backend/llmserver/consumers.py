import json
from channels.generic.websocket import AsyncWebsocketConsumer

class CommentaryConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()

    async def disconnect(self, close_code):
        pass

    # TODO: adapt to handle messages
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']

        # ...

        await self.send(text_data=json.dumps({
            'message': f"Received: {message}"
        }))
