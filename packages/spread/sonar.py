import os
import re

from openai import AsyncOpenAI

SONAR_API_KEY = os.getenv("SONAR_API_KEY")

client = AsyncOpenAI(api_key=SONAR_API_KEY, base_url="https://api.perplexity.ai")


async def execute_search(inquiry):
    messages = [
        {
            "role": "system",
            "content": (
                "Present the content as a series of claims, each of which contains all relevant context, and is unique."
                "Cite all sources, Do not include any claims which do not have a citation."
            ),
        },
        {
            "role": "user",
            "content": (
                inquiry
            ),
        },
    ]

    response = await client.chat.completions.create(
        model="sonar-reasoning-pro",
        messages=messages
    )
    result = response.choices[0].message.content
    match = re.match(r"^<think>(.*)</think>(.*)$", result, re.DOTALL)
    thought = match.group(1)
    content = match.group(2)
    citations = response.citations
    return thought, content, citations
