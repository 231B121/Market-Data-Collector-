"""HTTP client for the CoinGecko public REST API (read-only)."""

import logging
import time
from collections.abc import Sequence
from dataclasses import dataclass

import httpx

BASE_URL = "https://api.coingecko.com/api/v3"
DEFAULT_TIMEOUT_SECONDS = 10.0

logger = logging.getLogger(__name__)


class CoinGeckoError(Exception):
    """Raised when a CoinGecko request fails or returns unusable data."""


@dataclass(frozen=True)
class MarketsResponse:
    """Raw market data plus how long the API call took."""

    data: list[dict]
    latency_ms: float


class CoinGeckoClient:
    """Fetches market data from CoinGecko. Does no normalization."""

    def __init__(
        self,
        base_url: str = BASE_URL,
        timeout: float = DEFAULT_TIMEOUT_SECONDS,
        client: httpx.Client | None = None,
    ) -> None:
        self._base_url = base_url
        self._timeout = timeout
        self._client = client or httpx.Client()

    def fetch_markets(self, coin_ids: Sequence[str]) -> MarketsResponse:
        """Fetch USD market data for the given CoinGecko coin ids in ONE request."""
        if not coin_ids:
            raise CoinGeckoError("coin_ids must not be empty")

        url = f"{self._base_url}/coins/markets"
        params = {"vs_currency": "usd", "ids": ",".join(coin_ids)}

        start = time.perf_counter()
        try:
            response = self._client.get(url, params=params, timeout=self._timeout)
            latency_ms = (time.perf_counter() - start) * 1000
            response.raise_for_status()
            data = response.json()
        except httpx.TimeoutException as exc:
            raise CoinGeckoError(f"Request timed out after {self._timeout}s") from exc
        except httpx.HTTPStatusError as exc:
            raise CoinGeckoError(
                f"CoinGecko returned HTTP {exc.response.status_code}"
            ) from exc
        except httpx.RequestError as exc:
            raise CoinGeckoError(f"Network error: {exc}") from exc
        except ValueError as exc:
            raise CoinGeckoError("Response was not valid JSON") from exc

        if not isinstance(data, list):
            raise CoinGeckoError(f"Expected a list, got {type(data).__name__}")

        returned_ids = {item.get("id") for item in data}
        missing = [c for c in coin_ids if c not in returned_ids]
        if missing:
            logger.warning("Coins requested but not returned: %s", ", ".join(missing))

        return MarketsResponse(data=data, latency_ms=latency_ms)

    def close(self) -> None:
        """Release the underlying HTTP connection."""
        self._client.close()
