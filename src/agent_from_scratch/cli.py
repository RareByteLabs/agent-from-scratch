import argparse
import logging

from agent_from_scratch.agent import run_agent
from agent_from_scratch.config import load_settings


def main() -> None:
    parser = argparse.ArgumentParser(prog="agent-from-scratch", description="Evidence-lookup agent")
    parser.add_argument("question", help="A medical evidence question, in quotes")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    print(run_agent(load_settings(), args.question).answer)
