import os
import re

from openai import OpenAI

SONAR_API_KEY = os.getenv("SONAR_API_KEY")


async def execute_search(inquiry):
    messages = [
        {
            "role": "system",
            "content": (
                "You are an AI research assistant"
                "Be extremely thorough and provide as much detail as possible."
                "Cite all sources and provide a summary of any content relevant to the search query."
            ),
        },
        {
            "role": "user",
            "content": (
                inquiry
            ),
        },
    ]

    client = OpenAI(api_key=SONAR_API_KEY, base_url="https://api.perplexity.ai")

    # chat completion without streaming
    response = client.chat.completions.create(
        model="sonar-reasoning-pro",
        messages=messages,
    )
    result = response.choices[0].message.content
    match = re.match(r"^<think>(.*)</think>(.*)$", result, re.DOTALL)
    thought = match.group(1)
    content = match.group(2)
    citations = response.citations
    return thought, content, citations
