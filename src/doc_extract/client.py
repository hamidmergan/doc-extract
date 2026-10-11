"""Call an OpenAI-compatible server with an image."""

import base64

from .config import Settings
from .errors import ModelError


def make_client(settings: Settings):
    from openai import OpenAI

    return OpenAI(
        base_url=settings.base_url,
        api_key=settings.api_key,
        timeout=settings.timeout,
        max_retries=settings.max_retries,
    )


def transcribe_page(client, settings: Settings, png: bytes) -> str:
    data_url = "data:image/png;base64," + base64.b64encode(png).decode("ascii")
    try:
        response = client.chat.completions.create(
            model=settings.model,
            temperature=0,
            messages=[
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": settings.prompt},
                        {"type": "image_url", "image_url": {"url": data_url}},
                    ],
                }
            ],
        )
    except Exception as exc:
        raise ModelError(f"Request to {settings.base_url} failed: {exc}")
    try:
        content = response.choices[0].message.content
    except (AttributeError, IndexError, TypeError):
        raise ModelError("The server response has an unexpected format.")
    return (content or "").strip()
