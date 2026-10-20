"""Model catalogue and estimated cost. The data lives in prices.toml, not in code."""

import tomllib
from pathlib import Path

_MODELS = tomllib.loads(Path(__file__).with_name("prices.toml").read_text())


def cost_usd(model: str, tokens_in: int, tokens_out: int) -> float | None:
    """Return the estimated cost in USD, or None if the model has no price entry."""
    price = _MODELS.get(model)
    if price is None:
        return None
    return (tokens_in * price["input"] + tokens_out * price["output"]) / 1_000_000


def list_models() -> list[dict[str, str]]:
    """Models the interface may offer: [{"id": ..., "label": ...}, ...]."""
    return [{"id": model_id, "label": entry["label"]} for model_id, entry in _MODELS.items()]
