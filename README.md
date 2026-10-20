# agent-from-scratch: an evidence assistant, built from scratch

A small, production-minded example of an AI agent. You ask a medical-evidence question; the agent searches
[PubMed](https://pubmed.ncbi.nlm.nih.gov/) through the public NCBI API, reads the abstracts, and answers with PMID
citations. It runs from the command line or as a small web page with a model picker, live progress, and
token and cost readouts.

**Step-by-step tutorial:** [`docs/tutorial.html`](docs/tutorial.html). It walks through building this project from an empty folder
and includes a Q&A section. If GitHub Pages is enabled for this repo, read it at
`https://rarebytelabs.github.io/agent-from-scratch//tutorial.html`.

> **Demonstration project.** Answers can be incomplete or wrong. Verify every citation against the paper. This is not medical advice,
> and you should never enter patient-identifying information: questions are sent to a third-party API.

## What it shows

- The core agent pattern: a model in a loop with a tool (`tool_use` → run the tool → `tool_result` → repeat until `end_turn`)
- Engineering habits: typed code, linting, secrets kept out of git, pinned dependencies, one file that talks to the SDK
- Cost control in layers: step cap, tool-output cap, per-request prompt budget, cost estimate per run, console spend limits
- A thin web layer with server-side validation, an access code, safe rendering of model output, and streamed progress

## Requirements

- macOS or Linux, [uv](https://docs.astral.sh/uv/) (it installs Python 3.12 for you), and git
- An [Anthropic API key](https://console.anthropic.com/). Create it inside a Console Workspace with a small monthly spend limit.

## Setup

```bash
git clone https://github.com/<your-username>/<repo-name>.git
cd <repo-name>
uv sync                       # creates .venv and installs the pinned dependencies
cp .env.example .env          # then put your real key in .env
```

`.env` is gitignored. Never commit it.

| Variable | Required | Purpose |
|---|---|---|
| `ANTHROPIC_API_KEY` | yes | Your API key |
| `AGENT_MODEL` | no | Default model ID (default: `claude-haiku-4-5-20251001`) |
| `AGENT_ACCESS_CODE` | no | If set, the web page asks for this code before it will run a question |

## Run it

All commands run from the project root (the folder containing `pyproject.toml`).

**Ask a question from the command line**

```bash
uv run agent "Does screening colonoscopy reduce colorectal cancer mortality?"
```

The log shows each step, then the answer, then token usage and estimated cost.

**Try a different model without changing code**

```bash
AGENT_MODEL=claude-haiku-5-5 uv run agent "Do statins reduce cardiovascular events in primary prevention?"
```

**Start the web page**

```bash
uv run uvicorn agent_from_scratch.server:app --host 127.0.0.1 --port 8000
```

Open <http://127.0.0.1:8000>. Pick a model, type a question, and watch the progress steps appear. The page also shows
the model used, tokens in and out, estimated cost and time. Stop the server with `Ctrl+C`.

Listening on `127.0.0.1` means only your own machine can reach it. To let someone else try it, see chapter 11 of the tutorial
(Tailscale share or Funnel). If the server is reachable from the internet, set `AGENT_ACCESS_CODE` first.

**Test the PubMed tool on its own (no AI, no API key needed)**

```bash
uv run python -c "from agent_from_scratch.tools import search_pubmed; print(search_pubmed('colorectal cancer screening', 2)[:1500])"
```

**Check the code**

```bash
uv run ruff format .          # format
uv run ruff check .           # lint
uv run pytest                 # tests (a test suite is on the roadmap)
```

## Project layout

```
├── README.md
├── docs/tutorial.html         the step-by-step guide
├── pyproject.toml             dependencies, the `agent-from-scratch` command, ruff config
├── uv.lock                    exact dependency versions (committed on purpose)
├── .env.example               names of the variables; no secrets
└── src/agent_from_scratch/
    ├── config.py              settings from the environment
    ├── llm.py                 the only file that talks to the Anthropic SDK
    ├── tools.py               search_pubmed and its tool schema
    ├── agent.py               the agent loop, progress events, result object
    ├── pricing.py             cost estimate
    ├── prices.toml            model list and prices (data, not code)
    ├── cli.py                 command-line entry point
    ├── server.py              web layer (FastAPI)
    └── static/index.html      the web page
```

## Notes on cost

Costs shown are estimates at list prices from `src/agent_from_scratch/prices.toml` (last checked 2026-10-19). Prices change, so verify them on the
[Anthropic pricing page](https://platform.claude.com/docs/en/about-claude/pricing), and treat the Console usage page as the billing truth.

## Roadmap

- A small known-answer test set to evaluate answer quality when the prompt or model changes
- `pytest` tests for the cost function, event stream and prompt-budget guard
- Stricter system prompt: separate randomized-trial evidence from observational evidence
- CI that runs `ruff` and `pytest` on every push

## License

Add a license before publishing (for example MIT) as `LICENSE` in the project root.
