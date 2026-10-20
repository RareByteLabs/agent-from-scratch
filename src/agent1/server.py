"""HTTP interface for the agent. A thin layer: all agent logic stays in agent.py."""

import logging
import os
import secrets
from dataclasses import asdict, replace
from pathlib import Path
from typing import Annotated

import anthropic
from fastapi import FastAPI, Header, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from agent1.agent import run_agent
from agent1.config import load_settings
from agent1.pricing import list_models

logging.basicConfig(level=logging.INFO, format="%(message)s")
logging.getLogger("httpx").setLevel(logging.WARNING)
log = logging.getLogger(__name__)

STATIC_DIR = Path(__file__).with_name("static")
ACCESS_CODE = os.environ.get("AGENT1_ACCESS_CODE", "")  # empty means no code required

settings = load_settings()
MODELS = list_models()
ALLOWED_MODELS = {m["id"] for m in MODELS}

app = FastAPI(title="agent1", docs_url=None, redoc_url=None)


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


@app.post("/api/ask")
def ask(
    req: AskRequest, x_access_code: Annotated[str | None, Header()] = None
) -> dict[str, object]:
    # A plain `def` (not async): FastAPI runs it in a worker thread, so the
    # blocking agent call does not freeze the server for other requests.
    check_access(x_access_code)
    if req.model not in ALLOWED_MODELS:  # never trust the browser's dropdown value
        raise HTTPException(status_code=422, detail="Unknown model.")
    try:
        result = run_agent(replace(settings, model=req.model), req.question)
    except anthropic.APIError:
        log.exception("Anthropic API call failed")
        raise HTTPException(
            status_code=502, detail="The model service returned an error. Try again shortly."
        ) from None
    return asdict(result)
