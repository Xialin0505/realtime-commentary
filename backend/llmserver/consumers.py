import json
import os
import redis
import logging
import base64
import requests
import asyncio
import cv2
import os
import re
from channels.generic.websocket import AsyncWebsocketConsumer
from openai import AsyncOpenAI
from django.conf import settings
from dotenv import load_dotenv
import numpy as np

logger = logging.getLogger(__name__)
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)
idx = 0

segment_size = 40

load_dotenv()

client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

prompt = [
    """ You are a professional fencing commentator. Based on the image provided and the style of the following reference transcript, generate real-time, energetic, and insightful commentary suitable for a live broadcast. Describe the action visible in the image using correct fencing terms (e.g., lunge, parry, riposte, fleche). Keep the commentary concise, vivid, and fast-paced. Include fencer names, score dynamics, or momentum if visually inferable.
    Include emotional stakes, tactical insight, and real-time action. Match the tone of a dramatic sports broadcast given the reference transcript. If the picture does not have two people wearing white suit (Fencer),
    holding the weapon, then provide a summary or tactic of the game so far. If the piste lights up, track the score. 
    Either describe the image or provide tactical insight. keep track of the score. Consider not only the current pictures but also the previous five conversation.
    
    Reference Commentary:
    {}
    """,
    """ Generate a detailed, live fencing commentary for a fencing match. Based on the image provided and the style of the following reference transcript, generate real-time, energetic, and insightful commentary suitable for a live broadcast. Describe the action visible in the image using correct fencing terms (e.g., lunge, parry, riposte, fleche). Keep the commentary concise, vivid, and fast-paced. Include fencer names, score dynamics, or momentum if visually inferable.
    Provide tactical insight. Match the tone of a dramatic sports broadcast given the reference transcript. Consider not only the current pictures but also the previous five conversation.

    Reference Commentary:
    {}
    """,
    """ Generate a detailed, live fencing commentary for a fencing match. Based on the image provided and the style of the following reference transcript, generate real-time, energetic, and insightful commentary suitable for a live broadcast. Describe the action visible in the image using correct fencing terms (e.g., lunge, parry, riposte, fleche). Keep the commentary concise, vivid, and fast-paced. Include fencer names, score dynamics, or momentum if visually inferable.
        Include emotional stakes, tactical insight, and real-time action. Can include the time left, the current scoring, and the score both team need to win the game, or the tactic Fencer is taking.
        Match the tone of a dramatic sports broadcast given the reference transcript. Consider not only the current pictures but also the previous five conversation.

    Reference Commentary:
    {} 
    """
]

def read_transcript(folder_path):
    result = []
    for filename in os.listdir(folder_path):
        if filename.endswith('.txt'):
            file_path = os.path.join(folder_path, filename)
            with open(file_path, 'r', encoding='utf-8') as f:
                text = f.read()

            paragraphs = [p.strip() for p in text.split('\n') if p.strip()]
            for para in paragraphs:
                result.append(para)

    return result

async def start_up(transcript):

    stream = await client.chat.completions.create(
        model="gpt-4o",
        temperature=0.8,
        messages = 
        [
            {
                "role": "system", 
                "content": """provide the fencing commentary for all the following conversation in this session, 
                                using the given transcript as example. """},
            {
                "role": "user", 
                "content": "".join(transcript)}
        ]
    )

    print("Done providing the context")

transcript = read_transcript("./dataset/transcript")
number = len(transcript)

asyncio.run(start_up(transcript))

class OpenAIBatchGenerator:
    def __init__(self, prompt_list, transcript, segment_size=20, batch_size=1):
        self.prompt_list = prompt_list
        self.transcript = transcript
        self.segment_size = segment_size
        self.batch_size = batch_size
        self.buffer = []
        self.idx = 0
        self.total = len(transcript)

    def get_image_info(self, image_path):
        """Returns base64 and MIME type"""
        _, ext = os.path.splitext(image_path)
        ext = ext.lower()[1:]
        mime = f"image/{ext}" if ext in ["jpeg", "jpg", "png"] else None
        if not mime:
            return None, None
        with open(image_path, "rb") as f:
            b64 = base64.b64encode(f.read()).decode("utf-8")
        return b64, mime

    async def add_image(self, image_path):
        """Add image and yield only when buffer is full"""
        img_b64, img_type = self.get_image_info(image_path)
        if not img_b64 or not img_type:
            yield "Error: Invalid image."
            return
        
        self.buffer.append((img_b64, img_type))
        logger.info(f"[OpenAI-Batch] Buffered {len(self.buffer)}/{self.batch_size} image(s).")

        if len(self.buffer) < self.batch_size:
            return

        # Prepare transcript context
        start_idx = self.idx
        end_idx = min(self.total, self.idx + self.segment_size)
        context_text = "".join(self.transcript[start_idx:end_idx])

        # update idx for next batch
        if end_idx == self.total:
            self.idx = 0
        else:
            self.idx = (self.idx + self.segment_size) % self.total

        # choose prompt
        prompt_idx = 0
        if end_idx % 3 == 0:
            prompt_idx = 1
        elif end_idx % 8 == 0:
            prompt_idx = 2
        selected_prompt = self.prompt_list[prompt_idx]

        # Construct OpenAI message with image_url format
        image_contents = [
            {"type": "image_url", "image_url": {"url": f"data:{img_type};base64,{img_b64}"}}
            for img_b64, img_type in self.buffer
        ]

        try:
            stream = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": "You're a fencing commentator. Respond professionally with the provided commentary example."},
                    {"role": "assistant", "content": "reference tone and format: " + context_text},
                    {"role": "user", "content": [{"type": "text", "text": selected_prompt.format(context_text)}] + image_contents}
                ],
                stream=True,
            )

            response_text = ""
            async for chunk in stream:
                content = chunk.choices[0].delta.content
                if content:
                    response_text += content

            self.buffer = []  # clear buffer after use

            if response_text.strip():
                yield response_text.strip()
            else:
                yield "No valid response generated."

        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            yield "Error: Failed to generate commentary."

generator = OpenAIBatchGenerator(prompt_list=prompt, transcript=transcript, segment_size=20, batch_size=4)

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
                        "timestamp": timestamp,
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
        formatted_timestamp = re.sub(r"[:.]", "_", timestamp)
        image_path = f"/mnt/media/image/{self.video_id}_frame_{formatted_timestamp}.png"
        
        with open(image_path, "wb") as f:
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
                    commentary = f"[{timestamp}] " + commentary

                with open("/mnt/media/text/" + os.path.basename(image_path).replace(".png", ".txt"), "w+") as f:
                    f.write(commentary)

                message = {
                    "type": "commentary",
                    "timestamp": timestamp,
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
            pass
            # try: # delete image after processing (uncomment if needed)
            #     os.remove(image_path)
            #     logger.info(f"Deleted temp file: {image_path}")
            # except Exception as e:
            #     logger.error(f"Failed to delete temp file {image_path}: {e}")

    async def broadcast_message(self, event):
        """Sends a broadcast message to WebSocket clients."""
        try:
            logger.info(f"Broadcasting message: {event['message']}")
            await self.send(text_data=json.dumps(event["message"]))
        except Exception as e:
            logger.error(f"Failed to send broadcast message: {e}")
