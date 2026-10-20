from agent1.config import load_settings
from agent1.llm import ask


def main() -> None:
    settings = load_settings()
    print(ask(settings, "In one sentence, what is an AI agent?"))
