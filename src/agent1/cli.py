import argparse
import logging

from agent1.agent import run_agent
from agent1.config import load_settings


def main() -> None:
    parser = argparse.ArgumentParser(prog="agent1", description="Evidence-lookup agent")
    parser.add_argument("question", help="A medical evidence question, in quotes")
    args = parser.parse_args()
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    logging.getLogger("httpx").setLevel(logging.WARNING)
    print(run_agent(load_settings(), args.question))
