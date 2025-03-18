from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse, StreamingHttpResponse
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI

import json
import requests
import numpy as np
import cv2

import base64
import re
import os
import asyncio
import time
import numbers

load_dotenv()

def convert_image_to_base64(image_path):
    """Converts an image to Base64 string."""

    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    return encoded_string.decode('utf-8')

def get_image_info(img_name):

    img_url = settings.IMAGE_ROOT + '/' + img_name

    _, file_extension = os.path.splitext(img_url)
    file_extension = file_extension[1:]

    img_type = ""
    if (file_extension == "jpeg"):
        img_type = "image/jpeg"
    elif (file_extension == "png"):
        img_type = "image/png"
    elif (file_extension == "gif"):
        img_type = "image/gif"

    return convert_image_to_base64(img_url), img_type

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

        # print(type(img_bytes))  # Output: <class 'bytes'>

        # Optional: Save to file for checking
        # with open('output.png', 'wb') as f:
        #     f.write(img_bytes)
    else:
        return None

    return img_bytes


### Using Async for realtime API ###
async def async_openai_generator(img_name):
    prompt = """
                provide an appropriate, one-sentence, concise commentary for this picture to 
                entertain the audience that is natural and does not delve into too many details. 
                Consider not only the current game state but also the previous three game states. 
                This comment will be used as part of the live commentary system, along with other past and future messages. 
            """
    
    img_b64_str, img_type = get_image_info(img_name)

    if not img_type or not img_b64_str:
        yield "Error: image not found"
        return

    client = AsyncOpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),  # This is the default and can be omitted
    )

    stream = await client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{img_type};base64,{img_b64_str}"},
                    },
                ],
            }
        ],
        model="gpt-4o",
        stream=True,
    )

    async for chunk in stream:
        yield chunk.choices[0].delta.content or ""
        time.sleep(0.1)

def async_openai_request(request):
    img_name = request.GET.get('img_name')
    return StreamingHttpResponse(async_openai_generator(img_name))

### Streaming non-realtime ###
def sync_openai_generator(img_name):
    prompt = """
                provide an appropriate, one-sentence, concise commentary for this picture to 
                entertain the audience that is natural and does not delve into too many details. 
                Consider not only the current game state but also the previous three game states. 
                This comment will be used as part of the live commentary system, along with other past and future messages. 
            """

    img_b64_str, img_type = get_image_info(img_name)

    if not img_type or not img_b64_str:
        yield "Error: image not found"
        return
    
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),  # This is the default and can be omitted
    )

    stream = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:{img_type};base64,{img_b64_str}"},
                    },
                ],
            }
        ],
        model="gpt-4o",
        stream=True,
    )

    for chunk in stream:
        yield chunk.choices[0].delta.content or ""
        time.sleep(0.1)

def sync_openai_request(img_name):
    return StreamingHttpResponse(sync_openai_generator(img_name))

def self_deployed_ai(img_name):
    # Replace with your VM's external IP
    url = "http://{}:8000/inference_file".format(os.environ.get("DEEPSEEK_IP"))

    # Construct the conversation payload as a JSON string.
    # The conversation should have an image placeholder for the image you are sending.
    payload = {
        "conversation": [
            {
                "role": "User",
                "content": "<image_placeholder> Provide a professional commentary about this fencing game.",
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

    img_url = settings.IMAGE_ROOT + '/' + img_name

    img_data = process_img_compress(img_url)
    if not img_data:
        return HttpResponse({"image not found or not valid"})

    # Open your image file (make sure the path is correct).
    files = {"file": img_data}

    # Send a multipart/form-data POST request with the JSON payload as a form field.
    data = {"payload": payload_str}

    response = requests.post(url, data=data, files=files)

    response_json = response.json()
    description = json.dumps(response_json['response'], indent=4)

    return HttpResponse(description)
    

### The real generator API ###
### request URL: http://127.0.0.1:8000/generate/?img_name=xxx.png ###
def llmserver(request):
    img_name = request.GET.get('img_name')
    #return sync_openai_request(img_name)
    return self_deployed_ai(img_name)