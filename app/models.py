"""Normalized data models shared across the service."""

from dataclasses import asdict, dataclass
from datetime import datetime


@dataclass(frozen=True)
class MarketRecord:
    """One normalized market snapshot for a single coin."""

    symbol: str                     # e.g. "BTC-USD"
    exchange: str                   # always "coingecko"
    price: float                    # current USD price
    bid: float | None               # not provided by CoinGecko public API
    ask: float | None               # not provided by CoinGecko public API
    spread: float | None            # ask - bid
    spread_pct: float | None        # spread / mid_price * 100
    volume_24h: float | None        # 24h trading volume in USD
    price_change_24h_pct: float | None  # 24h change in percent
    api_latency_ms: float           # API round-trip time
    polled_at: datetime             # timezone-aware UTC
    raw_response_id: str | None = None

    def to_dict(self) -> dict:
        """Return a JSON-friendly dict (datetime as ISO 8601 string)."""
        data = asdict(self)
        data["polled_at"] = self.polled_at.isoformat()
        return data