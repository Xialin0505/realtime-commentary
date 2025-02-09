from django.shortcuts import render
from django.conf import settings
from django.http import HttpResponse, StreamingHttpResponse
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI

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

### Using Async for realtime API ###
async def async_openai_generator(request):
    prompt = """
                provide an appropriate, one-sentence, concise commentary for this picture to 
                entertain the audience that is natural and does not delve into too many details. 
                Consider not only the current game state but also the previous three game states. 
                This comment will be used as part of the live commentary system, along with other past and future messages. 
            """
    
    img_sequence = request.GET.get('sequence')
    img_b64_str, img_type = get_image_info(img_sequence)

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
    return StreamingHttpResponse(async_openai_generator(request))

### Streaming non-realtime ###
def sync_openai_generator(request):
    prompt = """
                provide an appropriate, one-sentence, concise commentary for this picture to 
                entertain the audience that is natural and does not delve into too many details. 
                Consider not only the current game state but also the previous three game states. 
                This comment will be used as part of the live commentary system, along with other past and future messages. 
            """
    
    img_name = request.GET.get('img_name')
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

def sync_openai_request(request):
    return StreamingHttpResponse(sync_openai_generator(request))

### The real generator API ###
### request URL: http://127.0.0.1:8000/generate/?sequence=1 ###
def llmserver(request):
    return sync_openai_request(request)