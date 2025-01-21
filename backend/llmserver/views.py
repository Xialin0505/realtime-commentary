from django.shortcuts import render
from django.http import HttpResponse, StreamingHttpResponse
from dotenv import load_dotenv
from openai import OpenAI, AsyncOpenAI

import base64
import re
import os
import asyncio
import time

load_dotenv()

def convert_image_to_base64(image_path):
    """Converts an image to Base64 string."""

    with open(image_path, "rb") as image_file:
        encoded_string = base64.b64encode(image_file.read())
    return encoded_string.decode('utf-8')

def get_image_info(image_path):
    filename, file_extension = os.path.splitext(image_path)
    file_extension = file_extension[1:]

    img_type = ""
    if (file_extension == "jpeg"):
        img_type = "image/jpeg"
    elif (file_extension == "png"):
        img_type = "image/png"
    elif (file_extension == "gif"):
        img_type = "image/gif"

    return convert_image_to_base64(image_path), img_type

### TO-DO ###
### Using Async for realtime API ###
async def async_openai_generator():
    client = AsyncOpenAI()

    async with client.beta.realtime.connect(model="gpt-4o-realtime-preview") as connection:
        await connection.session.update(session={'modalities': ['text']})

        await connection.conversation.item.create(
            item={
                "type": "message",
                "role": "user",
                "content": [{"type": "input_text", "text": "Say hello!"}],
            }
        )

        await connection.response.create()

        async for event in connection:
            if event.type == 'response.text.delta':
                print(event.delta, flush=True, end="")

            elif event.type == 'response.text.done':
                print()

            elif event.type == "response.done":
                break

def async_openai_request(request):
    asyncio.run(async_openai_generator())

### Streaming non-realtime ###
def sync_openai_generator(request):
    prompt = """
                provide an appropriate, one-sentence, concise commentary for this picture to 
                entertain the audience that is natural and does not delve into too many details. 
                Consider not only the current game state but also the previous three game states. 
                This comment will be used as part of the live commentary system, along with other past and future messages. 
            """
    
    img_sequence = request.GET.get('sequence')
    img_url = "./image/image" + img_sequence + ".png"
    img_b64_str, img_type = get_image_info(img_url)
    
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