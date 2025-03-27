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

logger = logging.getLogger(__name__)
REDIS_HOST = os.getenv("REDIS_HOST", "redis")
redis_client = redis.Redis(host=REDIS_HOST, port=6379, db=0, decode_responses=True)
idx = 0

segment_size = 20

load_dotenv()

client = AsyncOpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

prompt = [
    """ <image_placeholder> provide an professional, one or two sentence commentary for this fencing event like a real commetary for 
the audience that is natural and does not delve into too many details. If the picture does not have two people wearing white suit (Fencer),
holding the weapon, then provide a summary or tactic of the game so far. If the piste lights up, track the score. 
Either describe the image or provide tactical insight. keep track of the score.
Consider not only the current pictures but also the previous three conversation. Keep it brief. """,
"""
provide an professional, one or two sentence commentary for this fencing event like a real commetary for 
the audience that is natural and does not delve into too many details. Give out the tactic of the fencers.
"""
    """ <image_placeholder> provide an professional, one sentence commentary for this fencing game picture, by providing
        a summary of the game so far with no more than three sentence. Can include the time left, the current
        scoring, and the score both team need to win the game, or the tactic Fencer is taking. """
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

async def provide_transcript(transcript):

    stream = await client.chat.completions.create(
        model="gpt-4o",
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

transcript = read_transcript("../dataset/transcript")
number = len(transcript)

asyncio.run(provide_transcript(transcript))

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

def process_img_compress(img_path):
    with open(img_path, 'rb') as f:
        img_bytes = f.read()

    # Step 2: Convert bytes to NumPy array
    img_array = np.frombuffer(img_bytes, np.uint8)

    # Step 3: Decode image (BGR format)
    img = cv2.imdecode(img_array, cv2.IMREAD_COLOR)  # Shape: [H, W, 3]

    # Step 4: Resize to (384, 384) if needed
    img_resized = cv2.resize(img, (384, 384))  # Shape: [384, 384, 3]

    # Step 5: Transpose to [3, 384, 384] (channels first)
    img_transposed = np.transpose(img_resized, (2, 0, 1))  # Shape: [3, 384, 384]

    # Step 6: Add a fourth channel (ones)
    new_channel = np.ones((1, 384, 384), dtype=img_transposed.dtype)

    # Step 7: Concatenate to [4, 384, 384]
    img_final = np.concatenate((img_transposed, new_channel), axis=0)

    img_final = np.transpose(img_final, (1, 2, 0))

    if img_final.dtype != np.uint8:
        img_final = img_final.astype(np.uint8)

    # Step 1: Encode image (supports alpha channel)
    success, encoded_img = cv2.imencode('.jpg', img_final)

    if success:
        # Step 2: Get binary data
        img_bytes = encoded_img.tobytes()
    else:
        return None

    return img_bytes

async def async_deepseek_generator(image_path):
    # Replace with your VM's external IP
    url = "http://{}:8000/inference_file".format(os.environ.get("DEEPSEEK_IP"))

    # Construct the conversation payload as a JSON string.
    # The conversation should have an image placeholder for the image you are sending. 
    payload = {
        "conversation": [
            {
                "role": "User",
                "content": prompt[0],
                "images": []  # Empty list; image will be provided in the file upload.
            },
            {
                "role": "Assistant",
                "content": "",
            }
        ]
    }

    # Convert payload to JSON string.
    payload_str = json.dumps(payload)

    img_data = process_img_compress(image_path)

    # Open your image file (make sure the path is correct).
    files = {"file": img_data}

    # Send a multipart/form-data POST request with the JSON payload as a form field.
    data = {"payload": payload_str}

    response = requests.post(url, data=data, files=files)
    response_json = response.json()
    logger.info(response_json)
    yield response_json['response']

async def async_openai_generator(image_path):
    """Generates live commentary for the given image using OpenAI's API."""
    gpt_prompt = """
                provide an professional, one or two sentence commentary for this fencing event like a real commetary for 
the audience that is natural and does not delve into too many details. If the picture does not have two people wearing white suit (Fencer),
holding the weapon, then provide a summary or tactic of the game so far. If the piste lights up, track the score. 
Either describe the image, provide tactical insight or track the score.
Consider not only the current pictures but also the previous three conversation. Keep it brief.
            """

    img_b64_str, img_type = get_image_info(image_path)
    if not img_b64_str or not img_type:
        yield "Error: Image not found."
        return
    
    logger.info(f"Sending image to OpenAI, size: {len(img_b64_str)} bytes")

    global idx
    global transcript

    start_idx = idx
    end_idx = min(number, idx + segment_size)
    if end_idx == number:
        idx = 0
    else:
        idx = (idx + segment_size) % number

    prompt_idx = 0
    if end_idx % 3 == 0:
        prompt_idx = 1
    elif end_idx % 8 == 0:
        prompt_idx = 2

    try:
        stream = await client.chat.completions.create(
            model="gpt-4o",
            
            messages=[
                {
                    "role": "system", 
                    "content": "You're a fencing commentator. Respond professionally with the provided commentary example."
                },
                {
                    "role": "assistant", 
                    "content": "".join(transcript[start_idx:end_idx])
                },
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt[prompt_idx]},
                        {"type": "image_url", "image_url": {"url": f"data:{img_type};base64,{img_b64_str}"}},
                        {"type": "image_url", "image_url": {"url": f"data:{img_type};base64,{img_b64_str}"}},
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
        # yield "Error: Failed to generate commentary."
        yield

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
        
        with open("/mnt/backend/media/image/" + os.path.basename(image_path), "wb") as f:
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
            async for commentary in async_openai_generator(image_path):
                if timestamp:
                    commentary = f"[{timestamp:.2f}] " + commentary

                with open("/mnt/backend/media/text/" + os.path.basename(image_path).replace(".png", ".txt"), "w+") as f:
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
