from django.shortcuts import render
from django.http import HttpResponse, StreamingHttpResponse
from dotenv import load_dotenv

import os
import asyncio
import time
from openai import OpenAI, AsyncOpenAI

load_dotenv()

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
    prompt = "introduce your self"
    
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),  # This is the default and can be omitted
    )

    stream = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": prompt,
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
def llmserver(request):
    return sync_openai_request(request)