"""Estimated cost from token counts. Prices live in prices.toml, not in code."""

import tomllib
from pathlib import Path

_PRICES = tomllib.loads(Path(__file__).with_name("prices.toml").read_text())


def cost_usd(model: str, tokens_in: int, tokens_out: int) -> float | None:
    """Return the estimated cost in USD, or None if the model has no price entry."""
    price = _PRICES.get(model)
    if price is None:
        return None
    return (tokens_in * price["input"] + tokens_out * price["output"]) / 1_000_000
