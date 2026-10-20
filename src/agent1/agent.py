"""The agent loop: ask the model, run the tools it requests, feed results back, repeat."""

import logging

from anthropic.types import MessageParam, ToolParam, ToolResultBlockParam

from agent1.config import Settings
from agent1.llm import complete
from agent1.tools import SEARCH_PUBMED_SCHEMA, search_pubmed

log = logging.getLogger(__name__)

MAX_STEPS = 6  # hard stop so a confused agent can never loop (or spend) forever

SYSTEM_PROMPT = (
    "You are an evidence-lookup assistant for clinicians and health researchers. "
    "Answer questions about medical evidence by searching PubMed first. "
    "Base every claim on the abstracts you retrieved and cite the PMID for each one. "
    "If the evidence is weak, mixed or missing, say so plainly. "
    "Do not rely on memory for clinical claims."
)

TOOLS: list[ToolParam] = [SEARCH_PUBMED_SCHEMA]
TOOL_FUNCTIONS = {"search_pubmed": search_pubmed}


def run_tool(name: str, args: dict) -> str:
    func = TOOL_FUNCTIONS.get(name)
    if func is None:
        return f"Error: unknown tool '{name}'"
    try:
        return func(**args)
    except Exception as exc:  # report failures to the model instead of crashing the run
        log.exception("tool %s failed", name)
        return f"Error: {exc}"


def run_agent(settings: Settings, question: str) -> str:
    messages: list[MessageParam] = [{"role": "user", "content": question}]
    total_in = total_out = 0

    for step in range(1, MAX_STEPS + 1):
        response = complete(settings, system=SYSTEM_PROMPT, messages=messages, tools=TOOLS)
        total_in += response.usage.input_tokens
        total_out += response.usage.output_tokens
        log.info("step %d: stop_reason=%s", step, response.stop_reason)

        if response.stop_reason != "tool_use":
            log.info("tokens total: in=%d out=%d", total_in, total_out)
            return "".join(b.text for b in response.content if b.type == "text")

        messages.append({"role": "assistant", "content": response.content})
        results: list[ToolResultBlockParam] = []
        for block in response.content:
            if block.type == "tool_use":
                log.info("tool call: %s %s", block.name, block.input)
                results.append(
                    {
                        "type": "tool_result",
                        "tool_use_id": block.id,
                        "content": run_tool(block.name, block.input),
                    }
                )
        messages.append({"role": "user", "content": results})

    return "Stopped: step limit reached without a final answer."
