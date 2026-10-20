"""The agent loop: ask the model, run the tools it requests, feed results back, repeat."""

import logging
from dataclasses import dataclass

from anthropic.types import MessageParam, ToolParam, ToolResultBlockParam

from agent1.config import Settings
from agent1.llm import complete
from agent1.pricing import cost_usd
from agent1.tools import SEARCH_PUBMED_SCHEMA, search_pubmed

log = logging.getLogger(__name__)

MAX_STEPS = 6  # hard stop so a confused agent can never loop (or spend) forever

MAX_PROMPT_TOKENS = 60_000  # stay well below the 100K price threshold

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


def usage_summary(model: str, tokens_in: int, tokens_out: int) -> str:
    cost = cost_usd(model, tokens_in, tokens_out)
    cost_text = f"${cost:.4f}" if cost is not None else "unknown (no price on file)"
    return f"\n\n\nModel={model} tokens in={tokens_in} out={tokens_out} cost={cost_text}\n\n\n"


@dataclass(frozen=True)
class AgentResult:
    answer: str
    model: str
    tokens_in: int
    tokens_out: int
    cost_usd: float | None
    steps: int
    stopped_early: bool = False


def run_agent(settings: Settings, question: str) -> AgentResult:
    messages: list[MessageParam] = [{"role": "user", "content": question}]
    total_in = total_out = 0

    def finish(answer: str, steps: int, stopped_early: bool = False) -> AgentResult:
        log.info("usage: %s", usage_summary(settings.model, total_in, total_out))
        cost = cost_usd(settings.model, total_in, total_out)
        return AgentResult(answer, settings.model, total_in, total_out, cost, steps, stopped_early)

    for step in range(1, MAX_STEPS + 1):
        response = complete(settings, system=SYSTEM_PROMPT, messages=messages, tools=TOOLS)
        total_in += response.usage.input_tokens
        total_out += response.usage.output_tokens
        log.info("step %d: stop_reason=%s", step, response.stop_reason)

        if response.stop_reason != "tool_use":
            text = "".join(b.text for b in response.content if b.type == "text")
            return finish(text, step)

        if response.usage.input_tokens > MAX_PROMPT_TOKENS:
            log.warning("prompt size %d is over budget, stopping", response.usage.input_tokens)
            return finish("Stopped: prompt budget exceeded.", step, stopped_early=True)

        messages.append({"role": "assistant", "content": response.content})
        tool_results: list[ToolResultBlockParam] = []
        for block in response.content:
            if block.type == "tool_use":
                output = run_tool(block.name, block.input)
                tool_results.append(
                    {"type": "tool_result", "tool_use_id": block.id, "content": output}
                )
        messages.append({"role": "user", "content": tool_results})

    return finish("Stopped: step limit reached without a final answer.", MAX_STEPS, True)
