import json
import time
import os
import redis
import tempfile
import logging
import base64
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from openai import AsyncOpenAI
from django.conf import settings

logger = logging.getLogger(__name__)
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)

def convert_image_to_base64(image_path):
    """Converts an image to a Base64-encoded string."""
    with open(image_path, "rb") as image_file:
        return base64.b64encode(image_file.read()).decode("utf-8")

def get_image_info(image_path):
    """Returns the Base64 encoded image and its MIME type."""
    _, file_extension = os.path.splitext(image_path)
    file_extension = file_extension.lower()[1:]
    img_type = f"image/{file_extension}" if file_extension in ["jpeg", "jpg", "png"] else None
    return (convert_image_to_base64(image_path), img_type) if img_type else (None, None)

async def async_openai_generator(image_path):
    """Generates live commentary for the given image using OpenAI's API."""
    prompt = """
                provide an appropriate, one-sentence, concise commentary for this picture to 
                entertain the audience that is natural and does not delve into too many details. 
                Consider not only the current game state but also the previous three game states. 
                This comment will be used as part of the live commentary system, along with other past and future messages. 
            """

    img_b64_str, img_type = get_image_info(image_path)
    if not img_b64_str or not img_type:
        yield "Error: Image not found."
        return
    
    logger.info(f"Sending image to OpenAI, size: {len(img_b64_str)} bytes")

    client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

    try:
        stream = await client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {"type": "image_url", "image_url": {"url": f"data:{img_type};base64,{img_b64_str}"}},
                    ],
                }
            ],
            stream=True,
        )

        response_text = ""
        async for chunk in stream:
            content = chunk.choices[0].delta.content
            if content:
                response_text += content

        if response_text.strip():
            yield response_text.strip()
        else:
            yield "No valid response generated."

    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        yield "Error: Failed to generate commentary."

class CommentaryConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        """Handles new WebSocket connections."""
        self.video_id = self.scope["url_route"]["kwargs"]["video_id"]
        self.room_group_name = f"commentary_{self.video_id}"

        await self.channel_layer.group_add(self.room_group_name, self.channel_name)
        await self.accept()

        if redis_client:
            try:
                history = redis_client.lrange(f"commentary_{self.video_id}", 0, -1)
                for msg in history:
                    await self.send(text_data=msg)
            except Exception as e:
                logger.error(f"Failed to fetch latest commentary: {e}")

    async def disconnect(self, close_code):
        """Handles WebSocket disconnection."""
        await self.channel_layer.group_discard(self.room_group_name, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        """Handles incoming WebSocket messages."""
        try:
            if text_data:
                data = json.loads(text_data)
                if data.get("type") == "chat":
                    message = {
                        "type": "chat",
                        "timestamp": time.time(),
                        "username": data.get("username", "anonymous"),
                        "message": data["message"],
                    }
                    if redis_client:
                        try:
                            redis_client.rpush(f"chat_{self.video_id}", json.dumps(message))
                        except Exception as e:
                            logger.error(f"Failed to store chat message in Redis: {e}")

                    await self.channel_layer.group_send(
                        self.room_group_name, {"type": "broadcast_message", "message": message}
                    )

            elif bytes_data:
                await self.receive_bytes(bytes_data)

        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")

    async def receive_bytes(self, bytes_data):
        with tempfile.NamedTemporaryFile(delete=False, suffix=".png") as temp_file:
            temp_file.write(bytes_data)
            temp_file.flush()
            image_path = temp_file.name

        logger.info(f"Saved screenshot to {image_path}, checking file existence...")
        if not os.path.exists(image_path):
            logger.error("Failed to save screenshot!")
        else:
            logger.info("Screenshot successfully saved.")

        await self.process_screenshot(image_path)

    async def process_screenshot(self, image_path):
        """Processes an image and sends generated commentary to clients."""
        try:
            async for commentary in async_openai_generator(image_path):
                message = {
                    "type": "commentary",
                    "timestamp": time.time(),
                    "video_id": self.video_id,
                    "content": commentary,
                }

                logger.info(f"Generated commentary: {commentary}")

                if redis_client:
                    try:
                        redis_client.rpush(f"commentary_{self.video_id}", json.dumps(message))
                    except Exception as e:
                        logger.error(f"Failed to store commentary in Redis: {e}")

                await self.channel_layer.group_send(
                    self.room_group_name, {"type": "broadcast_message", "message": message}
                )
        finally:
            try:
                os.remove(image_path)
                logger.info(f"Deleted temp file: {image_path}")
            except Exception as e:
                logger.error(f"Failed to delete temp file {image_path}: {e}")

    async def broadcast_message(self, event):
        """Sends a broadcast message to WebSocket clients."""
        try:
            logger.info(f"Broadcasting message: {event['message']}")
            await self.send(text_data=json.dumps(event["message"]))
        except Exception as e:
            logger.error(f"Failed to send broadcast message: {e}")
