"""Thin wrapper around the Anthropic SDK. Everything else calls this, never the SDK directly."""

import anthropic

from agent1.config import Settings


def ask(settings: Settings, prompt: str) -> str:
    client = anthropic.Anthropic(api_key=settings.api_key)
    response = client.messages.create(
        model=settings.model,
        max_tokens=500,
        messages=[{"role": "user", "content": prompt}],
    )
    print(
        f"[tokens] in={response.usage.input_tokens} out={response.usage.output_tokens}"
    )
    return response.content[0].text
