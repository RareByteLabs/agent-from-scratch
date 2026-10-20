"""Token prices in USD per million tokens.

Source: https://platform.claude.com/docs/en/about-claude/pricing (checked 2026-10-19).
Prices change, so re-check before relying on these numbers.
Prompt-caching tokens are priced differently and are not handled here (we don't use caching).
"""

PRICES: dict[str, tuple[float, float]] = {
    # model id: (input $ per million tokens, output $ per million tokens)
    "claude-haiku-4-5-20251001": (1.0, 5.0),
    "claude-sonnet-5-5": (2.0, 10.0),
    "claude-sonnet-5": (2.0, 10.0),
    "claude-haiku-5-5": (0.10, 0.50),  # prompts over 100K tokens cost 0.50 / 2.50
}


def cost_usd(model: str, tokens_in: int, tokens_out: int) -> float | None:
    """Estimated cost of a run in USD, or None if we have no price for this model."""
    price = PRICES.get(model)
    if price is None:
        return None
    in_price, out_price = price
    return (tokens_in * in_price + tokens_out * out_price) / 1_000_000
