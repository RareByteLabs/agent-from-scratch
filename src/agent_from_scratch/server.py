"""HTTP interface for the agent. A thin layer: all agent logic stays in agent.py."""

import json
import logging
import os
import queue
import secrets
import threading
from collections.abc import Iterator
from dataclasses import asdict, replace
from pathlib import Path
from typing import Annotated

import anthropic
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel, Field

from agent_from_scratch.agent import run_agent
from agent_from_scratch.config import load_settings
from agent_from_scratch.pricing import list_models

logging.basicConfig(level=logging.INFO, format="%(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).with_name("static")
ACCESS_CODE = os.environ.get("AGENT_ACCESS_CODE", "")  # empty means no code required

settings = load_settings()
MODELS = list_models()
ALLOWED_MODELS = {m["id"] for m in MODELS}

app = FastAPI(title="agent-from-scratch", docs_url=None, redoc_url=None)


class AskRequest(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    model: str


def check_access(code: str | None) -> None:
    """Reject the request unless the shared access code matches (when one is configured)."""
    if ACCESS_CODE and not secrets.compare_digest(code or "", ACCESS_CODE):
        raise HTTPException(status_code=401, detail="Invalid access code.")


@app.get("/")
def index() -> FileResponse:
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/config")
def config() -> dict[str, object]:
    return {
        "models": MODELS,
        "default_model": settings.model,
        "access_required": bool(ACCESS_CODE),
    }


def event_stream(req: AskRequest) -> Iterator[str]:
    """Run the agent in a worker thread and yield its progress events as JSON lines."""
    events: queue.Queue[dict[str, object] | None] = queue.Queue()

    def worker() -> None:
        try:
            result = run_agent(
                replace(settings, model=req.model), req.question, on_event=events.put
            )
            events.put({"type": "done", "result": asdict(result)})
        except anthropic.APIError:
            log.exception("Anthropic API call failed")
            events.put({"type": "error", "detail": "The model service returned an error."})
        except Exception:  # noqa: BLE001 - boundary: report any failure to the client
            log.exception("Agent run failed")
            events.put({"type": "error", "detail": "Something went wrong on the server."})
        finally:
            events.put(None)  # sentinel: the stream is over

    threading.Thread(target=worker, daemon=True).start()
    while (event := events.get()) is not None:
        yield json.dumps(event) + "\n"


@app.post("/api/ask")
def ask(
    req: AskRequest, x_access_code: Annotated[str | None, Header()] = None
) -> StreamingResponse:
    # Checks happen before streaming starts, so failures are proper HTTP errors.
    check_access(x_access_code)
    if req.model not in ALLOWED_MODELS:  # never trust the browser's dropdown value
        raise HTTPException(status_code=422, detail="Unknown model.")
    return StreamingResponse(
        event_stream(req),
        media_type="application/x-ndjson",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
