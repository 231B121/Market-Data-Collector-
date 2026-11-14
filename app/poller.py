"""Background polling: fetch -> normalize -> save, repeated on an interval."""

import logging
import time
from collections.abc import Callable
from datetime import datetime, timezone

from app.clients.coingecko import CoinGeckoClient, CoinGeckoError
from app.rate_limiter import RateLimiter
from app.repository import MarketRepository, RepositoryError
from app.retry import retry
from app.services.normalizer import NormalizationError, normalize_market_item

logger = logging.getLogger(__name__)


class Poller:
    def __init__(
        self,
        client: CoinGeckoClient,
        repository: MarketRepository,
        rate_limiter: RateLimiter,
        pairs: tuple[str, ...],
        interval_seconds: int,
        sleep: Callable[[float], None] = time.sleep,
    ) -> None:
        self._client = client
        self._repo = repository
        self._limiter = rate_limiter
        self._pairs = pairs
        self._interval = interval_seconds
        self._sleep = sleep

    def _fetch(self):
        """One rate-limited request; retried only for temporary errors."""

        def attempt():
            self._limiter.wait()
            return self._client.fetch_markets(self._pairs)

        return retry(
            attempt,
            retry_on=(CoinGeckoError,),
            should_retry=lambda exc: exc.retryable,
            sleep=self._sleep,
        )

    def poll_once(self) -> int:
        """Run one cycle. Returns the number of records saved."""
        try:
            response = self._fetch()
        except CoinGeckoError as exc:
            logger.error("Poll failed: %s", exc)
            return 0

        polled_at = datetime.now(timezone.utc)
        saved = 0
        for item in response.data:
            try:
                record = normalize_market_item(
                    item, latency_ms=response.latency_ms, polled_at=polled_at
                )
                self._repo.save(record)
            except (NormalizationError, RepositoryError) as exc:
                logger.error("Skipping coin %s: %s", item.get("id"), exc)
                continue
            saved += 1
            logger.info(
                "Polled market data",
                extra={"symbol": record.symbol, "api_latency_ms": round(record.api_latency_ms, 1)},
            )
        return saved

    def run_forever(self) -> None:
        """Poll until interrupted (Ctrl+C)."""
        logger.info("Poller started: pairs=%s interval=%ss", ",".join(self._pairs), self._interval)
        try:
            while True:
                started = time.monotonic()
                self.poll_once()
                self._sleep(max(0.0, self._interval - (time.monotonic() - started)))
        except KeyboardInterrupt:
            logger.info("Poller stopped")