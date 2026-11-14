"""Convert raw CoinGecko market data into the normalized schema."""

from datetime import datetime, timezone

from app.models import MarketRecord

EXCHANGE_NAME = "coingecko"


class NormalizationError(Exception):
    """Raised when a raw item lacks data required to build a record."""


def _to_float(value: object) -> float | None:
    """Convert a number to float; return None if missing or not numeric."""
    if value is None or isinstance(value, bool):
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def calculate_spread(
    bid: float | None, ask: float | None
) -> tuple[float | None, float | None]:
    """Return (spread, spread_pct); both None if bid or ask is missing."""
    if bid is None or ask is None:
        return None, None
    spread = ask - bid
    mid_price = (bid + ask) / 2
    if mid_price == 0:
        return spread, None
    return spread, spread / mid_price * 100


def normalize_market_item(
    item: dict,
    latency_ms: float,
    polled_at: datetime | None = None,
    bid: float | None = None,
    ask: float | None = None,
) -> MarketRecord:
    """Turn one /coins/markets item into a MarketRecord."""
    raw_symbol = item.get("symbol")
    if not isinstance(raw_symbol, str) or not raw_symbol.strip():
        raise NormalizationError("Missing or invalid 'symbol' in API item")

    price = _to_float(item.get("current_price"))
    if price is None:
        raise NormalizationError(
            f"Missing or invalid 'current_price' for {raw_symbol!r}"
        )

    bid = _to_float(bid)
    ask = _to_float(ask)
    spread, spread_pct = calculate_spread(bid, ask)

    return MarketRecord(
        symbol=f"{raw_symbol.strip().upper()}-USD",
        exchange=EXCHANGE_NAME,
        price=price,
        bid=bid,
        ask=ask,
        spread=spread,
        spread_pct=spread_pct,
        volume_24h=_to_float(item.get("total_volume")),
        price_change_24h_pct=_to_float(item.get("price_change_percentage_24h")),
        api_latency_ms=latency_ms,
        polled_at=polled_at or datetime.now(timezone.utc),
        raw_response_id=None,
    )