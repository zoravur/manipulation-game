import os
from typing import Optional

from dotenv import load_dotenv
from openai import AsyncOpenAI

_client: Optional[AsyncOpenAI] = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is not None:
        return _client

    load_dotenv()
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise RuntimeError("OPENROUTER_API_KEY is missing. Add it to your .env file.")

    # OpenRouter's OpenAI-compatible endpoint.
    _client = AsyncOpenAI(
        api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        # Optional but recommended by OpenRouter.
        default_headers={
            "HTTP-Referer": "http://localhost",
            "X-Title": "manipulation-game-sample",
        },
    )
    return _client
