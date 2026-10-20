"""Thin wrapper around the Anthropic SDK. Everything else calls this, never the SDK directly."""

import anthropic
from anthropic.types import MessageParam, ToolParam

from agent1.config import Settings


def complete(
    settings: Settings,
    *,
    system: str,
    messages: list[MessageParam],
    tools: list[ToolParam],
    max_tokens: int = 1500,
) -> anthropic.types.Message:
    client = anthropic.Anthropic(api_key=settings.api_key)
    return client.messages.create(
        model=settings.model,
        max_tokens=max_tokens,
        system=system,
        messages=messages,
        tools=tools,
    )
