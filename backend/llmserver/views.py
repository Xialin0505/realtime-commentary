from django.shortcuts import render
from django.http import HttpResponse
from dotenv import load_dotenv

import os
from openai import OpenAI

load_dotenv()

def openai_request():
    prompt = ""
    
    client = OpenAI(
        api_key=os.environ.get("OPENAI_API_KEY"),  # This is the default and can be omitted
    )

    stream = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "introduce your self",
            }
        ],
        model="gpt-4o",
        stream=True,
    )

    content = ""

    for chunk in stream:
        content += chunk.choices[0].delta.content or ""

    return content


def llmserver(request):
    content = openai_request()
    return HttpResponse(content)