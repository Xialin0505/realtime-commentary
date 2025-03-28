import json
import time
import os
import redis
import tempfile
import logging
import base64
import requests
import asyncio
import cv2
import os
from channels.generic.websocket import AsyncWebsocketConsumer
from openai import AsyncOpenAI
from django.conf import settings
from dotenv import load_dotenv
import numpy as np
import random

logger = logging.getLogger(__name__)
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)

load_dotenv()

prompt = [
    """ provide an descriptive commentary or provide tactical insight, or tracks the score/status, with memory of
        the previous scene of this session. """,
    """ provide an professional, one sentence commentary for this fencing game picture, by providing
        the current score for the fencing game, who is the leading, and by how many score. """,
    """ provide an professional, one sentence commentary for this fencing game picture, by providing
        a summary of the game so far with no more than three sentence. Can include the time left, the current
        scoring, and the score both team need to win the game, or the tactic Fencer is taking. """
]

class DeepSeekBatchGenerator:
    def __init__(self, prompt, batch_size=4):
        self.buffer = []
        self.prompt = prompt
        self.batch_size = batch_size

    def process_img_compress(self, img_path):
        with open(img_path, 'rb') as f:
            img_bytes = f.read()

        img_array = np.frombuffer(img_bytes, np.uint8)
        img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)
        img_resized = cv2.resize(img, (384, 384))
        img_transposed = np.transpose(img_resized, (2, 0, 1))
        new_channel = np.ones((1, 384, 384), dtype=img_transposed.dtype)
        img_final = np.concatenate((img_transposed, new_channel), axis=0)
        img_final = np.transpose(img_final, (1, 2, 0))

        if img_final.dtype != np.uint8:
            img_final = img_final.astype(np.uint8)

        success, encoded_img = cv2.imencode('.jpg', img_final)
        return encoded_img.tobytes() if success else None

    async def add_image(self, image_path):
        self.buffer.append(self.process_img_compress(image_path))
        logger.info(f"Collected {len(self.buffer)} image(s).")

        if len(self.buffer) < self.batch_size:
            return
        
        # Local test
        # await asyncio.sleep(random.uniform(30, 50))
        # logger.info(f"response {len(self.buffer)}")
        # self.buffer = []
        # yield f"response {len(self.buffer)}"

        url = "http://{}:8000/inference_file".format(os.environ.get("DEEPSEEK_IP"))
        payload = {
            "conversation": [
                {
                    "role": "User",
                    "content":" ".join(["<image_placeholder>" for _ in range(self.batch_size)]) + f"{self.prompt}",
                    "images": ["<image>" for _ in range(self.batch_size)]
                },
                {
                    "role": "Assistant",
                    "content": "",
                }
            ]
        }
        payload_str = json.dumps(payload)

        files = [("files", img) for img in self.buffer]
        data = {"payload": payload_str}

        # Async version
        # async with httpx.AsyncClient() as client:
        #     response = await client.post(url, data=data, files=files)

        response = requests.post(url, data=data, files=files)
        logger.info(f"Collected {self.batch_size} image(s), sent to DeepSeek.")

        response_json = response.json()
        logger.info(response_json)

        self.buffer = []
        yield response_json['response']

generator = DeepSeekBatchGenerator(prompt=prompt[0])

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
                elif data.get("type") == "screenshot":
                    _, base64_str = data.get("image").split(",", 1)
                    bytes_data = bytearray(base64.b64decode(base64_str))
                    timestamp = data.get("timestamp")
                    await self.receive_bytes(bytes_data, timestamp)

            elif bytes_data:
                await self.receive_bytes(bytes_data)

        except Exception as e:
            logger.error(f"Error processing WebSocket message: {e}")

    async def receive_bytes(self, bytes_data, timestamp=0.0):
        timestamp_formatted = f"_{timestamp:.2f}".replace(".", "_")
        with tempfile.NamedTemporaryFile(delete=False, suffix=timestamp_formatted + ".png") as temp_file:
            temp_file.write(bytes_data)
            temp_file.flush()
            image_path = temp_file.name
        
        with open("/mnt/media/image/" + os.path.basename(image_path), "wb") as f:
            f.write(bytes_data)

        logger.info(f"Saved screenshot to {image_path}, checking file existence...")
        if not os.path.exists(image_path):
            logger.error("Failed to save screenshot!")
        else:
            logger.info("Screenshot successfully saved.")

        await self.process_screenshot(image_path, timestamp)

    async def process_screenshot(self, image_path, timestamp):
        """Processes an image and sends generated commentary to clients."""
        try:
            async for commentary in generator.add_image(image_path):

                if timestamp:
                    commentary = f"[{timestamp:.2f}] " + commentary

                with open("/mnt/media/text/" + os.path.basename(image_path).replace(".png", ".txt"), "w+") as f:
                    f.write(commentary)

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
