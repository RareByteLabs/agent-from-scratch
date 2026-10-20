"""Settings come from the environment, loaded in one place, failing fast."""

import os
from dataclasses import dataclass

from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    api_key: str
    model: str


def load_settings() -> Settings:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError(
            "ANTHROPIC_API_KEY is not set. Copy .env.example to .env and fill it in."
        )
    return Settings(
        api_key=api_key,
        model=os.environ.get("AGENT_MODEL", "claude-haiku-5-5"),
    )
