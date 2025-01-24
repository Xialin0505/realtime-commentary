import json
from channels.generic.websocket import AsyncWebsocketConsumer

class CommentaryConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        await self.send(text_data=json.dumps({"message": "Hello, WebSocket!"}))

    async def disconnect(self, close_code):
        print(f"WebSocket closed with code {close_code}")  # Debugging
        pass  

    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data.get("message", "")
        print(f"Received: {message}")  # Debugging
        await self.send(text_data=json.dumps({"message": f"You said: {message}"}))
